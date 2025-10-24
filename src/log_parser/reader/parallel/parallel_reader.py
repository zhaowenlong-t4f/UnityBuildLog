"""Parallel file reader implementation."""

from typing import Optional, List, Dict, Any
from concurrent.futures import as_completed
import logging
import time
import threading
from pathlib import Path

from ..base import LogFileHandler, ReaderContext, ReadResult
from .thread_pool import ThreadPool
from .task_manager import TaskManager, FileChunk
from .load_balancer import LoadBalancer
from .error_handler import ErrorHandler
from ..monitoring.stats_collector import StatsCollector

stats_collector = StatsCollector()

logger = logging.getLogger(__name__)

class ParallelReader:
    """并行文件读取器实现。"""
    
    def __init__(
        self,
        context: ReaderContext,
        file_handler: LogFileHandler,
        max_workers: int = 4
    ):
        """初始化并行读取器。

        Args:
            context: 读取器上下文
            file_handler: 文件处理器
            max_workers: 最大工作线程数
        """
        self._context = context
        self._file_handler = file_handler
        self._thread_pool = ThreadPool(max_workers=max_workers)
        self._task_manager = TaskManager(chunk_size=context.chunk_size)
        self._load_balancer = LoadBalancer(
            initial_workers=max_workers // 2,
            max_workers=max_workers
        )
        self._error_handler = ErrorHandler()
        self._is_initialized = False
        self._worker_tasks: Dict[int, str] = {}  # worker_id -> current_task_id
        
    def initialize(self) -> None:
        """初始化并行处理环境。"""
        if self._is_initialized:
            return
            
        self._thread_pool.start()
        self._file_handler.open()
        self._is_initialized = True
        logger.info("Parallel reader initialized")
        
    def close(self) -> None:
        """关闭并行读取器。"""
        if self._is_initialized:
            self._thread_pool.stop()
            self._file_handler.close()
            self._worker_tasks.clear()
            self._is_initialized = False
            logger.info("Parallel reader closed")
            
    def get_worker_stats(self) -> Dict[str, Any]:
        """获取工作线程统计信息。
        
        Returns:
            Dict[str, Any]: 包含性能统计的字典
        """
        stats = {
            "workers": {},
            "unhealthy_workers": self._load_balancer.get_unhealthy_workers(),
            "optimal_chunk_size": self._load_balancer.get_optimal_chunk_size(),
            "active_workers": len(self._worker_tasks)
        }
        
        for worker_id in self._worker_tasks.keys():
            worker_health = self._load_balancer.get_worker_health(worker_id)
            if worker_health:
                stats["workers"][str(worker_id)] = worker_health
                
        return stats
            
    def read_chunks(self) -> List[ReadResult]:
        """并行读取文件块。

        Returns:
            List[ReadResult]: 读取结果列表，按块顺序排列

        Raises:
            RuntimeError: 如果读取器未初始化
            OSError: 如果发生IO错误
        """
        if not self._is_initialized:
            raise RuntimeError("Parallel reader not initialized")
            
        # 准备任务
        chunk_count = self._task_manager.prepare_file_tasks(str(self._context.file_path))
        logger.info(f"Prepared {chunk_count} chunks for parallel processing")
        
        # 提交任务并收集结果
        futures = []
        results: List[Optional[ReadResult]] = [None] * chunk_count
        
        while True:
            chunk = self._task_manager.get_next_task()
            if not chunk:
                break
                
            future = self._thread_pool.submit(self._process_chunk, chunk)
            futures.append((chunk.chunk_id, future))
            
        # 处理结果
        for chunk_id, future in futures:
            try:
                result = future.result()
                results[chunk_id] = result
                stats_collector.record_metric(
                    "parallel_chunk_processed",
                    1,
                    {"chunk_id": chunk_id}
                )
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_id}: {e}")
                raise
                
        # 清理任务管理器状态
        self._task_manager.clear()
        
        # 过滤并按块顺序返回结果
        valid_results = [r for r in results if r is not None]
        sorted_results = sorted(valid_results, key=lambda x: x.position)  # 按位置排序
        return sorted_results
        
    def _process_chunk(self, chunk: FileChunk) -> ReadResult:
        """处理单个文件块。

        Args:
            chunk: 要处理的文件块

        Returns:
            ReadResult: 处理结果
        """
        worker_id = hash(threading.get_ident()) % 10000  # 生成唯一的worker ID
        task_id = f"chunk_{chunk.chunk_id}"
        start_time = time.time()
        
        try:
            # 注册worker并记录任务
            self._load_balancer.register_worker(worker_id)
            self._worker_tasks[worker_id] = task_id
            
            stats_collector.record_metric(
                "parallel_chunk_start",
                1,
                {"chunk_id": chunk.chunk_id, "worker_id": worker_id}
            )
            
            # 使用负载均衡器获取优化的块大小
            optimal_chunk_size = self._load_balancer.get_optimal_chunk_size()
            if optimal_chunk_size != chunk.chunk_size:
                logger.debug(
                    f"Adjusting chunk size from {chunk.chunk_size} to "
                    f"{optimal_chunk_size} for worker {worker_id}"
                )
                chunk.chunk_size = min(
                    optimal_chunk_size,
                    Path(chunk.file_path).stat().st_size - chunk.start_pos
                )
            
            # 创建新的文件处理器实例
            thread_handler = type(self._file_handler)(self._context)
            thread_handler.open()
            thread_handler.seek(chunk.start_pos)
            content = thread_handler.read_bytes(chunk.chunk_size)
            thread_handler.close()
            
            result = ReadResult(
                content=content,
                position=chunk.start_pos,
                size=len(content),
                is_eof=(chunk.start_pos + len(content)) >= Path(chunk.file_path).stat().st_size,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "original_size": chunk.chunk_size,
                    "worker_id": worker_id
                }
            )
            
            # 更新性能统计
            processing_time = time.time() - start_time
            self._load_balancer.update_worker_stats(
                worker_id,
                processing_time,
                len(content)
            )
            
            stats_collector.record_metric(
                "parallel_chunk_complete",
                1,
                {
                    "chunk_id": chunk.chunk_id,
                    "worker_id": worker_id,
                    "bytes_read": len(content),
                    "processing_time": processing_time
                }
            )
            
            # 清理错误状态（如果之前有的话）
            self._error_handler.clear_error(task_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in chunk {chunk.chunk_id} (worker {worker_id}): {e}")
            
            # 更新错误统计
            processing_time = time.time() - start_time
            self._load_balancer.update_worker_stats(
                worker_id,
                processing_time,
                0,
                had_error=True
            )
            
            stats_collector.record_metric(
                "parallel_chunk_error",
                1,
                {
                    "chunk_id": chunk.chunk_id,
                    "worker_id": worker_id,
                    "error": str(e)
                }
            )
            
            # 处理错误并决定是否重试
            metadata = {
                "chunk_id": chunk.chunk_id,
                "worker_id": worker_id,
                "start_pos": chunk.start_pos,
                "chunk_size": chunk.chunk_size
            }
            
            if self._error_handler.handle_error(e, task_id, metadata):
                logger.info(f"Retrying chunk {chunk.chunk_id} with worker {worker_id}")
                return self._process_chunk(chunk)  # 重试
                
            raise