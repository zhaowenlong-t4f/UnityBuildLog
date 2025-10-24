"""GZIP文件处理器实现。"""

import gzip
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO

from .base import BaseFileHandler
from ..exceptions import FileFormatError, ReadError

class GzipFileHandler(BaseFileHandler):
    """GZIP文件处理器。
    
    处理GZIP压缩文件的读取，支持：
    1. 自动解压缩
    2. 流式读取
    3. 压缩元数据获取
    """
    
    def __init__(
        self,
        file_path: Path,
        buffer_size: int = 65536,  # 64KB默认缓冲区
        encoding: str = 'utf-8',
        errors: str = 'strict'
    ) -> None:
        """初始化GZIP文件处理器。

        Args:
            file_path: 压缩文件路径
            buffer_size: 解压缓冲区大小
            encoding: 文件编码
            errors: 编码错误处理方式

        Raises:
            FileNotFoundError: 文件不存在
            FileFormatError: 不是有效的GZIP文件
            PermissionError: 没有读取权限
            LookupError: 指定的编码不存在
        """
        super().__init__(file_path, buffer_size)
        self._gzip_file: Optional[gzip.GzipFile] = None
        self.encoding = encoding
        self.errors = errors
        
        # 验证编码
        try:
            'test'.encode(encoding)
        except LookupError as e:
            raise LookupError(f"不支持的编码格式 '{encoding}': {e}")
        
        # 验证GZIP文件格式
        try:
            with gzip.open(file_path, 'rb') as test_file:
                test_file.read(1)
        except gzip.BadGzipFile:
            raise FileFormatError(f"不是有效的GZIP文件：{file_path}")
            
    def open(self) -> None:
        """打开GZIP文件。

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 没有读取权限
            OSError: 其他IO错误
        """
        if self._is_open:
            return
            
        try:
            self._file = open(self.file_path, 'rb')
            self._gzip_file = gzip.GzipFile(
                fileobj=self._file,
                mode='rb'
            )
            self._is_open = True
            self._current_position = 0
        except Exception as e:
            if self._file is not None:
                self._file.close()
                self._file = None
            raise OSError(f"打开GZIP文件失败：{e}")
            
    def close(self) -> None:
        """关闭GZIP文件。"""
        if self._gzip_file is not None:
            try:
                self._gzip_file.close()
            finally:
                self._gzip_file = None
                
        super().close()
        
    def read(self, size: int = -1) -> str:
        """读取、解压和解码指定大小的数据。

        Args:
            size: 要读取的字节数，-1表示读取到文件末尾

        Returns:
            解压和解码后的字符串数据

        Raises:
            OSError: IO错误
            ValueError: size参数无效
            UnicodeDecodeError: 解码错误
        """
        if not self._is_open or self._gzip_file is None:
            raise OSError("文件未打开")
            
        if size < -1:
            raise ValueError("size参数必须大于等于-1")
            
        try:
            # 读取并解压数据
            data = self._gzip_file.read(size)
            
            # 更新位置（注意：这是解压后的位置）
            self._current_position = self._gzip_file.tell()
            
            # 解码数据
            return data.decode(self.encoding, errors=self.errors)
        except Exception as e:
            raise ReadError(f"读取GZIP文件失败：{e}")
            
    def get_metadata(self) -> Dict[str, Any]:
        """获取GZIP文件元数据。

        Returns:
            包含文件元数据的字典
        """
        if not self._is_open or self._gzip_file is None:
            self.open()
            
        try:
            return {
                "compressed_size": self.file_path.stat().st_size,
                "mtime": self._gzip_file.mtime,
                "compression_level": self._gzip_file.level if hasattr(self._gzip_file, 'level') else None,
                "buffer_size": self.buffer_size,
                "file_type": "gzip"
            }
        except Exception as e:
            raise OSError(f"获取GZIP元数据失败：{e}")