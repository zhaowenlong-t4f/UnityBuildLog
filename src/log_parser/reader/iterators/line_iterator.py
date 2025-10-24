"""
行迭代器实现，支持按行读取日志文件内容。

提供高效的按行读取功能，支持大行处理、行缓冲和行拆分规则。
使用惰性加载策略，减少内存使用。
"""
from typing import Optional, Iterator, List
from ..exceptions import ReadError

class LineIterator:
    """行迭代器，支持按行读取日志内容"""

    def __init__(self, file_handler, buffer_size: int = 4096, max_line_length: int = 1024 * 1024):
        """
        初始化行迭代器

        Args:
            file_handler: 文件处理器实例
            buffer_size: 读取缓冲区大小，默认4KB（根据性能测试结果优化）
            max_line_length: 最大行长度，默认1MB
        """
        self.file_handler = file_handler
        self.buffer_size = buffer_size
        self.max_line_length = max_line_length
        self._buffer = ""
        self._current_position = self.file_handler.tell()
        self._line_number = 0

    def __iter__(self) -> Iterator[str]:
        """返回迭代器自身"""
        return self

    def __next__(self) -> str:
        """
        获取下一行内容

        Returns:
            str: 下一行的内容

        Raises:
            StopIteration: 当到达文件末尾时
            ReadError: 当读取过程中发生错误时
        """
        try:
            line = self._read_line()
            if line is None:
                raise StopIteration
            self._line_number += 1
            self._current_position = self.file_handler.tell()
            return line
        except StopIteration:
            raise
        except Exception as e:
            raise ReadError(f"读取行时发生错误: {str(e)}")

    def _read_line(self) -> Optional[str]:
        """
        读取一行内容

        Returns:
            Optional[str]: 读取的行内容，如果到达文件末尾则返回None
        """
        while True:
            # 检查是否超过最大行长度
            if len(self._buffer) >= self.max_line_length:
                # 强制拆分行，但不添加额外的换行符
                line = self._buffer[:self.max_line_length]
                self._buffer = self._buffer[self.max_line_length:]
                if not line.endswith('\n'):
                    return line

            # 在缓冲区中查找换行符
            newline_pos = self._buffer.find('\n')
            if newline_pos != -1:
                # 找到换行符，返回一行（包含换行符）
                line = self._buffer[:newline_pos + 1]
                self._buffer = self._buffer[newline_pos + 1:]
                return line

            # 读取更多内容到缓冲区
            chunk = self.file_handler.read(self.buffer_size)
            if not chunk:
                # 文件结束，返回剩余的缓冲区内容
                if self._buffer:
                    line = self._buffer
                    self._buffer = ""
                    return line if line.endswith('\n') else line + '\n'
                return None

            self._buffer += chunk

    def reset(self):
        """重置迭代器状态"""
        self._buffer = ""
        self._current_position = 0
        self._line_number = 0
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
        self._buffer = ""
        self._line_number = 0
        self.file_handler.seek(position)

    def get_line_number(self) -> int:
        """
        获取当前行号

        Returns:
            int: 当前行号
        """
        return self._line_number