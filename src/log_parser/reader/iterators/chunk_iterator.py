"""
分片迭代器实现，用于高效处理大文件。

支持按照固定大小（默认8MB）进行文件分片读取，提供高效的大文件处理能力。
具有分片边界处理和分片合并策略，确保日志内容的完整性。支持文本和二进制模式。
"""
from typing import Optional, Iterator, List, Union, BinaryIO, TextIO, Any
from ..exceptions import ReadError

class ChunkIterator:
    """分片迭代器，支持大文件的高效处理"""

    def _is_binary_mode(self) -> bool:
        """判断是否是二进制模式打开的文件"""
        # 检查文件处理器的实际类型，并尝试获取mode属性
        mode = getattr(self.file_handler, 'mode', None)
        if mode is not None:
            return 'b' in mode
        return isinstance(self.file_handler, BinaryIO)

    def _ensure_type(self, data: Union[str, bytes, None], is_binary: bool) -> Union[str, bytes]:
        """确保数据类型与文件模式匹配
        
        Args:
            data: 需要确保类型的数据
            is_binary: 是否需要二进制类型
            
        Returns:
            Union[str, bytes]: 转换后的数据
        """
        if data is None:
            return b"" if is_binary else ""
            
        if is_binary:
            if isinstance(data, str):
                return data.encode('utf-8')
            elif isinstance(data, bytes):
                return data
            else:
                return str(data).encode('utf-8')
        else:
            if isinstance(data, bytes):
                return data.decode('utf-8')
            elif isinstance(data, str):
                return data
            else:
                return str(data)

    def __init__(self, file_handler: Union[BinaryIO, TextIO], chunk_size: Optional[int] = None):
        """
        初始化分片迭代器

        Args:
            file_handler: 文件处理器实例，支持二进制和文本模式
            chunk_size: 分片大小，如果为None则自动根据文件大小选择合适的大小
        """
        self.file_handler = file_handler
        
        # 根据文件大小自动选择chunk_size
        if chunk_size is None:
            try:
                if hasattr(self.file_handler, 'file_path'):
                    file_size = self.file_handler.file_path.stat().st_size
                else:
                    # 对于普通文件对象，尝试获取文件大小
                    import os
                    file_size = os.fstat(self.file_handler.fileno()).st_size
                # 文件大小的1/1000，但不小于64KB且不大于256KB
                auto_size = max(64 * 1024, min(file_size // 1000, 256 * 1024))
                self.chunk_size = auto_size
            except:
                # 如果无法获取文件大小，使用默认64KB
                self.chunk_size = 64 * 1024
        else:
            self.chunk_size = chunk_size

        # 初始化缓冲区和位置
        self._current_position = self.file_handler.tell()
        self._init_buffer()

    def __iter__(self) -> Iterator[Union[str, bytes]]:
        """返回迭代器自身"""
        return self

    def __next__(self) -> Union[str, bytes]:
        """
        获取下一个分片

        Returns:
            Union[str, bytes]: 下一个分片的内容，根据文件打开模式返回str或bytes

        Raises:
            StopIteration: 当到达文件末尾时
            ReadError: 当读取过程中发生错误时
        """
        try:
            chunk = self.file_handler.read(self.chunk_size)
            self._current_position = self.file_handler.tell()
            
            # 判断是否是二进制模式
            is_binary = self._is_binary_mode()
            empty = b"" if is_binary else ""
            
            if not chunk:
                if self._buffer:
                    # 返回最后的缓冲区内容并更新位置
                    last_chunk = self._ensure_type(self._buffer, is_binary)
                    self._buffer = empty
                    return last_chunk
                raise StopIteration

            # 确保数据类型正确
            chunk = self._ensure_type(chunk, is_binary)
                
            # 处理分片边界
            chunk = self._handle_chunk_boundary(chunk)
            if chunk:
                return chunk
            return next(self)  # 如果当前分片为空，尝试读取下一个分片

        except StopIteration:
            raise
        except Exception as e:
            raise ReadError(f"读取分片时发生错误: {str(e)}")

    def _handle_chunk_boundary(self, chunk: Union[str, bytes]) -> Union[str, bytes]:
        """
        处理分片边界，确保不会在行中间截断

        Args:
            chunk: 当前读取的分片内容

        Returns:
            Union[str, bytes]: 处理后的分片内容
        """
        if not chunk:
            return chunk

        # 判断是否是二进制模式
        is_binary = self._is_binary_mode()

        # 选择正确的换行符和空值
        newline = b'\n' if is_binary else '\n'
        empty = b"" if is_binary else ""
        
        # 强制确保正确的数据类型
        chunk = self._ensure_type(chunk, is_binary)
        self._buffer = self._ensure_type(self._buffer, is_binary)
        
        # 合并前检查是否以换行符结束
        # 如果已经以换行符结束，可以直接返回
        if chunk.endswith(newline) and not self._buffer:
            return chunk
            
        # 将之前的缓冲区内容添加到当前分片开头
        if self._buffer:
            chunk = self._buffer + chunk
            self._buffer = empty

        # 寻找最后一个换行符
        last_newline = chunk.rfind(newline)
        if last_newline != -1:
            # 将最后一个不完整的行保存到缓冲区
            self._buffer = chunk[last_newline + 1:]
            return chunk[:last_newline + 1]
        
        # 如果没有找到换行符，说明这个分片是一个非常长的行的一部分
        self._buffer = chunk
        return empty

    def _init_buffer(self):
        """初始化或重置缓冲区"""
        self._buffer = b"" if self._is_binary_mode() else ""
    
    def reset(self):
        """重置迭代器状态"""
        self._current_position = 0
        self._init_buffer()
        self.file_handler.seek(0)

    def tell(self) -> int:
        """
        获取当前文件位置

        Returns:
            int: 当前文件位置
        """
        return self._current_position

    def seek(self, position: int):
        """
        设置文件读取位置

        Args:
            position: 目标位置
        """
        self._current_position = position
        self._init_buffer()
        self.file_handler.seek(position)

    def __iter__(self) -> Iterator[Union[str, bytes]]:
        """返回迭代器自身"""
        return self