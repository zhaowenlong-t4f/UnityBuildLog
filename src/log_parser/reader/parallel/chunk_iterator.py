"""Parallel chunk iterator implementation."""

from typing import Iterator, Optional
from ..base import LogIterator, ReaderContext, LogFileHandler
from .parallel_reader import ParallelReader
import logging

logger = logging.getLogger(__name__)

class ParallelChunkIterator(LogIterator):
    """使用并行处理的块迭代器实现。"""
    
    def __init__(
        self,
        context: ReaderContext,
        file_handler: LogFileHandler,
        max_workers: Optional[int] = None
    ):
        """初始化并行块迭代器。

        Args:
            context: 读取器上下文
            file_handler: 文件处理器
            max_workers: 最大工作线程数
        """
        self._context = context
        self._file_handler = file_handler
        self._max_workers = max_workers or 4
        self._reader: Optional[ParallelReader] = None
        self._chunks = []
        self._current_index = 0
        
    def __iter__(self) -> Iterator[bytes]:
        """返回迭代器对象。

        Returns:
            Iterator[bytes]: 迭代器对象
        """
        self.reset()
        return self
        
    def __next__(self) -> bytes:
        """返回下一个数据块。

        Returns:
            bytes: 下一个数据块

        Raises:
            StopIteration: 当没有更多数据时
        """
        if self._current_index >= len(self._chunks):
            raise StopIteration
            
        chunk = self._chunks[self._current_index]
        self._current_index += 1
        return chunk.content
        
    def reset(self) -> None:
        """重置迭代器状态。"""
        self._initialize_if_needed()
        # 重置文件处理器的位置
        self._file_handler.seek(0)
        self._chunks = self._reader.read_chunks()
        self._current_index = 0
        logger.info(f"Iterator reset, loaded {len(self._chunks)} chunks")
        
    def _initialize_if_needed(self) -> None:
        """确保并行读取器已初始化。"""
        if self._reader is None:
            self._reader = ParallelReader(
                self._context,
                self._file_handler,
                max_workers=self._max_workers
            )
            self._reader.initialize()
            
    def close(self) -> None:
        """关闭迭代器和相关资源。"""
        if self._reader is not None:
            self._reader.close()
            self._reader = None