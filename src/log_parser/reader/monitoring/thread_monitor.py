"""线程性能监控模块。"""

import threading
from typing import Dict, Any, Optional
import time
import psutil
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ThreadStats:
    """线程统计信息。"""
    thread_id: int
    cpu_percent: float
    memory_usage: int
    io_read_bytes: int
    io_write_bytes: int
    start_time: float
    last_update: float
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_task_time: float

    def copy(self):
        """创建当前对象的副本。

        Returns:
            ThreadStats: 当前对象的副本
        """
        return ThreadStats(
            thread_id=self.thread_id,
            cpu_percent=self.cpu_percent,
            memory_usage=self.memory_usage,
            io_read_bytes=self.io_read_bytes,
            io_write_bytes=self.io_write_bytes,
            start_time=self.start_time,
            last_update=self.last_update,
            total_tasks=self.total_tasks,
            completed_tasks=self.completed_tasks,
            failed_tasks=self.failed_tasks,
            avg_task_time=self.avg_task_time
        )

class ThreadMonitor:
    """线程性能监控器。
    
    负责收集和分析线程级别的性能指标，包括：
    - CPU使用率
    - 内存使用
    - IO操作统计
    - 任务处理统计
    """
    
    def __init__(self):
        """初始化线程监控器。"""
        self._stats: Dict[int, ThreadStats] = {}
        self._lock = threading.Lock()
        self._process = psutil.Process()
        self._start_time = time.time()
        self._task_times = defaultdict(list)
        
    def register_thread(self, thread_id: Optional[int] = None) -> int:
        """注册新线程。

        Args:
            thread_id: 可选的线程ID，如果不提供则使用当前线程ID

        Returns:
            注册的线程ID
        """
        if thread_id is None:
            thread_id = threading.get_ident()
            
        with self._lock:
            if thread_id not in self._stats:
                self._stats[thread_id] = ThreadStats(
                    thread_id=thread_id,
                    cpu_percent=0.0,
                    memory_usage=0,
                    io_read_bytes=0,
                    io_write_bytes=0,
                    start_time=time.time(),
                    last_update=time.time(),
                    total_tasks=0,
                    completed_tasks=0,
                    failed_tasks=0,
                    avg_task_time=0.0
                )
                logger.info(f"Registered thread {thread_id} for monitoring")
                
        return thread_id
        
    def start_task(self, thread_id: int, task_id: str):
        """记录任务开始。

        Args:
            thread_id: 线程ID
            task_id: 任务ID
        """
        with self._lock:
            if thread_id in self._stats:
                self._stats[thread_id].total_tasks += 1
                self._task_times[task_id] = time.time()
                
    def end_task(self, thread_id: int, task_id: str, success: bool = True):
        """记录任务结束。

        Args:
            thread_id: 线程ID
            task_id: 任务ID
            success: 任务是否成功完成
        """
        with self._lock:
            if thread_id in self._stats and task_id in self._task_times:
                stats = self._stats[thread_id]
                task_time = time.time() - self._task_times[task_id]
                
                # 更新统计
                if success:
                    stats.completed_tasks += 1
                else:
                    stats.failed_tasks += 1
                    
                # 更新平均任务时间
                total_completed = stats.completed_tasks + stats.failed_tasks
                if total_completed > 0:
                    stats.avg_task_time = (
                        (stats.avg_task_time * (total_completed - 1) + task_time)
                        / total_completed
                    )
                    
                del self._task_times[task_id]
                
    def update_stats(self, thread_id: int):
        """更新线程统计信息。

        Args:
            thread_id: 线程ID
        """
        with self._lock:
            if thread_id not in self._stats:
                return
                
            stats = self._stats[thread_id]
            current_time = time.time()
            time_diff = current_time - stats.last_update
            
            try:
                # 获取线程CPU和内存使用情况
                thread = psutil.Process(thread_id)
                stats.cpu_percent = thread.cpu_percent() / psutil.cpu_count()
                stats.memory_usage = thread.memory_info().rss
                
                # 获取IO统计
                io_counters = thread.io_counters()
                stats.io_read_bytes = io_counters.read_bytes
                stats.io_write_bytes = io_counters.write_bytes
                
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"无法获取线程 {thread_id} 的性能数据: {e}")
                
            stats.last_update = current_time
            
    def get_thread_stats(self, thread_id: int) -> Optional[Dict[str, Any]]:
        """获取线程统计信息。

        Args:
            thread_id: 线程ID

        Returns:
            统计信息字典或None（如果线程未注册）
        """
        with self._lock:
            if thread_id not in self._stats:
                return None
            stats = self._stats[thread_id].copy()

        # 在锁外计算派生值
        return {
            "thread_id": stats.thread_id,
            "cpu_percent": stats.cpu_percent,
            "memory_usage_mb": stats.memory_usage / (1024 * 1024),
            "io_read_mb": stats.io_read_bytes / (1024 * 1024),
            "io_write_mb": stats.io_write_bytes / (1024 * 1024),
            "uptime_seconds": time.time() - stats.start_time,
            "total_tasks": stats.total_tasks,
            "completed_tasks": stats.completed_tasks,
            "failed_tasks": stats.failed_tasks,
            "success_rate": (
                stats.completed_tasks / stats.total_tasks
                if stats.total_tasks > 0 else 0
            ),
            "avg_task_time": stats.avg_task_time
        }
            
    def get_all_stats(self) -> Dict[int, Dict[str, Any]]:
        """获取所有线程的统计信息。

        Returns:
            所有线程的统计信息字典
        """
        with self._lock:
            thread_ids = list(self._stats.keys())
            
        return {
            thread_id: self.get_thread_stats(thread_id)
            for thread_id in thread_ids
        }
            
    def clear_stats(self, thread_id: int):
        """清除线程统计信息。

        Args:
            thread_id: 线程ID
        """
        with self._lock:
            if thread_id in self._stats:
                del self._stats[thread_id]
                logger.info(f"Cleared stats for thread {thread_id}")
                
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取总体性能摘要。

        Returns:
            性能统计摘要
        """
        # 获取数据快照
        with self._lock:
            stats_snapshot = [stats.copy() for stats in self._stats.values()]
            start_time = self._start_time
            
        # 在锁外计算汇总数据
        total_tasks = sum(stats.total_tasks for stats in stats_snapshot)
        completed_tasks = sum(stats.completed_tasks for stats in stats_snapshot)
        failed_tasks = sum(stats.failed_tasks for stats in stats_snapshot)
        total_cpu = sum(stats.cpu_percent for stats in stats_snapshot)
        total_memory = sum(stats.memory_usage for stats in stats_snapshot)
        total_io_read = sum(stats.io_read_bytes for stats in stats_snapshot)
        total_io_write = sum(stats.io_write_bytes for stats in stats_snapshot)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - start_time,
            "active_threads": len(stats_snapshot),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (
                completed_tasks / total_tasks if total_tasks > 0 else 0
            ),
            "total_cpu_percent": total_cpu,
            "total_memory_mb": total_memory / (1024 * 1024),
            "total_io_read_mb": total_io_read / (1024 * 1024),
            "total_io_write_mb": total_io_write / (1024 * 1024)
        }