"""文件处理器基类实现。"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, TYPE_CHECKING, Union
from pathlib import Path

from ..exceptions import FileFormatError, ReadError

if TYPE_CHECKING:
    from ..base import ReaderContext

class BaseFileHandler(ABC):
    """文件处理器基类。
    
    提供基本的文件操作功能和资源管理。所有具体的文件处理器都应该继承此类。
    """
    
    def __init__(self, file_path: Union[Path, str, 'ReaderContext'], buffer_size: int = 4096) -> None:
        """初始化文件处理器。

        Args:
            file_path: 文件路径或ReaderContext实例
            buffer_size: 读取缓冲区大小

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 没有读取权限
        """
        # 如果是ReaderContext，提取file_path和buffer_size
        if hasattr(file_path, 'file_path'):
            self.context = file_path
            self.buffer_size = getattr(file_path, 'buffer_size', buffer_size)
            file_path = file_path.file_path
        else:
            self.context = None
            self.buffer_size = buffer_size
            
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        self.file_path = file_path
        self.path = file_path  # 兼容性别名
        self._file: Optional[BinaryIO] = None
        self._is_open = False
        self._current_position = 0
        self._cache_manager = None
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在：{self.file_path}")
        if not self.file_path.is_file():
            raise FileFormatError(f"不是有效的文件：{self.file_path}")
            
    def __enter__(self) -> 'BaseFileHandler':
        """上下文管理器入口。"""
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出。"""
        self.close()
        
    @property
    def is_open(self) -> bool:
        """文件是否打开。"""
        return self._is_open
        
    @property
    def current_position(self) -> int:
        """当前文件位置。"""
        return self._current_position
        
    def open(self) -> None:
        """打开文件。

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 没有读取权限
            OSError: 其他IO错误
        """
        if self._is_open:
            return
            
        try:
            self._file = open(self.file_path, 'rb')
            self._is_open = True
            self._current_position = 0
        except (FileNotFoundError, PermissionError) as e:
            raise e
        except Exception as e:
            raise OSError(f"打开文件失败：{e}")
            
    def close(self) -> None:
        """关闭文件。"""
        if self._file is not None:
            try:
                self._file.close()
            finally:
                self._file = None
                self._is_open = False
                
    def seek(self, offset: int, whence: int = 0) -> int:
        """移动文件指针位置。

        Args:
            offset: 偏移量
            whence: 位置基准（0-文件开头，1-当前位置，2-文件末尾）

        Returns:
            新的文件位置

        Raises:
            OSError: IO错误
            ValueError: 参数无效
        """
        if not self._is_open:
            raise OSError("文件未打开")
            
        try:
            position = self._file.seek(offset, whence)
            self._current_position = position
            return position
        except Exception as e:
            raise OSError(f"seek操作失败：{e}")
            
    def tell(self) -> int:
        """获取当前文件位置。

        Returns:
            当前位置的字节偏移量

        Raises:
            OSError: IO错误
        """
        if not self._is_open:
            raise OSError("文件未打开")
            
        try:
            position = self._file.tell()
            self._current_position = position
            return position
        except Exception as e:
            raise OSError(f"tell操作失败：{e}")
            
    @abstractmethod
    def read(self, size: int = -1) -> bytes:
        """读取文件内容。

        Args:
            size: 要读取的字节数，-1表示读取到文件末尾

        Returns:
            读取的字节数据

        Raises:
            OSError: IO错误
            ValueError: size参数无效
        """
        pass
        
    def set_cache_manager(self, cache_manager) -> None:
        """设置缓存管理器。
        
        Args:
            cache_manager: CacheManager实例
        """
        self._cache_manager = cache_manager