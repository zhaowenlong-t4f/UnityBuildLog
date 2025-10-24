"""
Memory monitoring and management system.
"""
import os
import gc
import psutil
import threading
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from threading import Lock

@dataclass
class MemoryThreshold:
    warning: float = 0.8  # 80% 警告阈值
    critical: float = 0.9  # 90% 严重阈值

@dataclass
class MemorySnapshot:
    timestamp: float
    total: int
    used: int
    percent: float

class MemoryMonitor:
    """Monitors memory usage and manages memory-related operations."""

    def __init__(self, threshold: float = 0.8, sampling_interval: float = 5.0):
        self._threshold = MemoryThreshold(warning=threshold)
        self._sampling_interval = sampling_interval
        self._lock = Lock()
        self._snapshots: List[MemorySnapshot] = []
        self._process = psutil.Process(os.getpid())
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self) -> None:
        """Start the memory monitoring thread."""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop the memory monitoring thread."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
            self._monitor_thread = None

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            self._take_snapshot()
            time.sleep(self._sampling_interval)

    def _take_snapshot(self) -> None:
        """Take a snapshot of current memory usage."""
        memory_info = self._process.memory_info()
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total=psutil.virtual_memory().total,
            used=memory_info.rss,
            percent=memory_info.rss / psutil.virtual_memory().total
        )
        
        with self._lock:
            self._snapshots.append(snapshot)
            # 保持最近100个采样点
            if len(self._snapshots) > 100:
                self._snapshots.pop(0)

    def check_memory_usage(self) -> float:
        """检查当前内存使用率。"""
        memory_info = self._process.memory_info()
        return memory_info.rss / psutil.virtual_memory().total

    def should_trigger_gc(self) -> bool:
        """判断是否需要触发垃圾回收。"""
        usage = self.check_memory_usage()
        return usage > self._threshold.warning

    def get_memory_trend(self) -> List[Dict[str, Any]]:
        """获取内存使用趋势数据。"""
        with self._lock:
            return [
                {
                    "timestamp": snapshot.timestamp,
                    "used_mb": snapshot.used / (1024 * 1024),
                    "percent": snapshot.percent
                }
                for snapshot in self._snapshots
            ]

    def detect_memory_leak(self, window_size: int = 10) -> bool:
        """
        检测是否存在内存泄漏。
        通过分析最近window_size个采样点的趋势来判断。
        """
        with self._lock:
            if len(self._snapshots) < window_size:
                return False

            recent_snapshots = self._snapshots[-window_size:]
            initial_used = recent_snapshots[0].used
            final_used = recent_snapshots[-1].used
            
            # 如果内存持续增长超过10%，可能存在泄漏
            growth_rate = (final_used - initial_used) / initial_used
            return growth_rate > 0.1

    def force_garbage_collection(self) -> None:
        """强制执行垃圾回收。"""
        gc.collect()
    
    def check_memory(self) -> float:
        """check_memory_usage 的别名，用于兼容性。"""
        return self.check_memory_usage()