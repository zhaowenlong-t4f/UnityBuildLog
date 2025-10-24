"""文本文件处理器实现。"""

from pathlib import Path
from typing import Optional, Dict, Any

from .base import BaseFileHandler
from ..exceptions import ReadError

class TextFileHandler(BaseFileHandler):
    """文本文件处理器。
    
    处理普通文本文件的读取，支持：
    1. 按字节读取
    2. 编码处理
    3. 基本的缓冲管理
    """
    
    def __init__(
        self,
        file_path: Path,
        encoding: str = 'utf-8',
        buffer_size: int = 4096,
        errors: str = 'strict'
    ) -> None:
        """初始化文本文件处理器。

        Args:
            file_path: 文件路径
            encoding: 文件编码
            buffer_size: 读取缓冲区大小
            errors: 编码错误处理方式（'strict', 'ignore', 'replace'等）

        Raises:
            FileNotFoundError: 文件不存在时
            PermissionError: 没有读取权限时
            LookupError: 指定的编码不存在
        """
        super().__init__(file_path, buffer_size)
        self.encoding = encoding
        self.errors = errors
        self._decoder = None
        self._buffer = bytearray()
        
        # 验证编码
        try:
            'test'.encode(encoding)
        except LookupError as e:
            raise LookupError(f"不支持的编码格式 '{encoding}': {e}")
            
    def read_bytes(self, size: int = -1) -> bytes:
        """读取指定大小的原始字节数据。

        Args:
            size: 要读取的字节数，-1表示读取到文件末尾

        Returns:
            字节数据

        Raises:
            OSError: IO错误
            ValueError: size参数无效
        """
        if not self._is_open:
            raise OSError("文件未打开")
            
        if size < -1:
            raise ValueError("size参数必须大于等于-1")
            
        try:
            # 直接读取指定大小
            if size == -1:
                data = self._file.read()
            else:
                data = self._file.read(size)
                
            # 更新位置
            self._current_position = self._file.tell()
            return data
        except Exception as e:
            raise ReadError(f"读取文件失败：{e}")

    def read(self, size: int = -1) -> str:
        """读取并解码指定大小的数据。

        Args:
            size: 要读取的字节数，-1表示读取到文件末尾

        Returns:
            解码后的字符串数据

        Raises:
            OSError: IO错误
            ValueError: size参数无效
            UnicodeDecodeError: 解码错误
        """
        if not self._is_open:
            raise OSError("文件未打开")
            
        if size < -1:
            raise ValueError("size参数必须大于等于-1")
            
        try:
            # 直接读取指定大小
            if size == -1:
                data = self._file.read()
            else:
                data = self._file.read(size)
                
            # 更新位置
            self._current_position = self._file.tell()
            
            # 解码数据并规范化行尾
            text = data.decode(self.encoding, errors=self.errors)
            text = text.replace('\r\n', '\n')
            
            # 如果是完整读取，则缓存数据
            if size == -1 and self._cache_manager is not None:
                self._cache_manager.put(str(self.file_path), text)
                
            return text
        except Exception as e:
            raise ReadError(f"读取文件失败：{e}")
            
    def get_metadata(self) -> Dict[str, Any]:
        """获取文件元数据。

        Returns:
            包含文件元数据的字典
        """
        return {
            "encoding": self.encoding,
            "buffer_size": self.buffer_size,
            "errors": self.errors,
            "file_size": self.file_path.stat().st_size,
            "file_type": "text"
        }