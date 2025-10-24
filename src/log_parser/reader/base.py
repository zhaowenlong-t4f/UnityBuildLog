"""Base classes and interfaces for the log reader module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Any, Dict, Optional
from pathlib import Path

@dataclass
class ReadResult:
    """表示读取操作的结果。"""
    
    content: bytes  # 读取的内容
    position: int   # 当前读取位置
    size: int      # 读取的字节数
    is_eof: bool   # 是否到达文件末尾
    metadata: Dict[str, Any]  # 额外的元数据信息

class ReaderContext:
    """日志读取器的上下文环境。

    负责维护读取过程中的状态信息，包括：
    - 文件路径
    - 编码设置
    - 缓冲区大小
    - 当前位置等
    """
    
    def __init__(
        self,
        file_path: Path,
        encoding: str = 'utf-8',
        buffer_size: int = 8192,
        chunk_size: int = 8 * 1024 * 1024,  # 8MB
    ) -> None:
        """初始化读取器上下文。

        Args:
            file_path: 日志文件路径
            encoding: 文件编码
            buffer_size: 读取缓冲区大小
            chunk_size: 分片大小
        """
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.buffer_size = buffer_size
        self.chunk_size = chunk_size
        self.position = 0
        self.total_bytes_read = 0
        self.is_closed = False
        self._metadata: Dict[str, Any] = {}

    @property
    def metadata(self) -> Dict[str, Any]:
        """获取上下文的元数据。"""
        return self._metadata

    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据。

        Args:
            key: 元数据键
            value: 元数据值
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取指定的元数据。

        Args:
            key: 元数据键
            default: 默认值，当键不存在时返回

        Returns:
            元数据值或默认值
        """
        return self._metadata.get(key, default)

    def reset(self) -> None:
        """重置上下文状态。"""
        self.position = 0
        self.total_bytes_read = 0
        self.is_closed = False
        self._metadata.clear()
        
    def update_from_config(self, config: Dict[str, Any]) -> None:
        """从配置更新上下文参数。

        Args:
            config: 配置字典
        """
        if 'encoding' in config:
            self.encoding = config['encoding']
        if 'buffer_size' in config:
            self.buffer_size = config['buffer_size']
        if 'chunk_size' in config:
            self.chunk_size = config['chunk_size']

class LogFileHandler(ABC):
    """日志文件处理器的抽象基类。"""
    
    @abstractmethod
    def open(self) -> None:
        """打开文件准备读取。

        Raises:
            FileNotFoundError: 文件不存在时
            PermissionError: 没有读取权限时
            OSError: 其他IO错误
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭文件。

        Raises:
            OSError: IO错误
        """
        pass
    
    @abstractmethod
    def read(self, size: int = -1) -> bytes:
        """从文件中读取数据。

        Args:
            size: 要读取的字节数，-1表示读取到文件末尾

        Returns:
            读取的字节数据

        Raises:
            OSError: IO错误
            ValueError: size参数无效
        """
        pass

    @abstractmethod
    def seek(self, offset: int, whence: int = 0) -> int:
        """移动文件读取位置。

        Args:
            offset: 偏移量
            whence: 位置基准（0表示文件开头，1表示当前位置，2表示文件末尾）

        Returns:
            新的绝对位置

        Raises:
            OSError: IO错误
            ValueError: 参数无效
        """
        pass

    @abstractmethod
    def tell(self) -> int:
        """获取当前文件位置。

        Returns:
            当前位置的字节偏移量

        Raises:
            OSError: IO错误
        """
        pass

class LogIterator(ABC):
    """日志迭代器的抽象基类。"""
    
    @abstractmethod
    def __iter__(self) -> Iterator[Any]:
        """返回迭代器对象。

        Returns:
            迭代器对象
        """
        pass
    
    @abstractmethod
    def __next__(self) -> Any:
        """返回迭代的下一项。

        Returns:
            下一个日志项

        Raises:
            StopIteration: 迭代结束
            OSError: IO错误
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """重置迭代器到初始状态。

        Raises:
            OSError: IO错误
        """
        pass