"""
Stats Collector for monitoring system performance metrics.
"""
from typing import Dict, Any, List
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional, Any

@dataclass
class IOStats:
    bytes_read_total: int = 0
    read_operations: int = 0
    total_time: float = 0.0
    start_time: float = field(default_factory=time.time)

    @property
    def read_speed_mbps(self) -> float:
        elapsed = time.time() - self.start_time
        if elapsed <= 0:
            return 0.0
        return (self.bytes_read_total / (1024 * 1024)) / elapsed

    @property
    def avg_read_latency(self) -> float:
        if self.read_operations == 0:
            return 0.0
        return self.total_time / self.read_operations

@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    total_lookups: int = 0

    @property
    def hit_ratio(self) -> float:
        if self.total_lookups == 0:
            return 0.0
        return self.hits / self.total_lookups

class StatsCollector:
    """Collects and manages performance statistics for the log reader."""
    
    def __init__(self):
        self._lock = Lock()
        self._io_stats = IOStats()
        self._cache_stats = CacheStats()
        self._operation_latencies: Dict[str, List[float]] = {}

    def collect_io_stats(self, bytes_read: int, time_taken: float) -> None:
        """Collect statistics about IO operations."""
        with self._lock:
            self._io_stats.bytes_read_total += bytes_read
            self._io_stats.read_operations += 1
            self._io_stats.total_time += time_taken

    def record_cache_hit(self) -> None:
        """记录一次缓存命中。"""
        with self._lock:
            self._cache_stats.total_lookups += 1
            self._cache_stats.hits += 1
            
    def record_cache_miss(self) -> None:
        """记录一次缓存未命中。"""
        with self._lock:
            self._cache_stats.total_lookups += 1
            self._cache_stats.misses += 1

    def collect_operation_latency(self, operation: str, latency: float) -> None:
        """Collect latency information for specific operations."""
        with self._lock:
            if operation not in self._operation_latencies:
                self._operation_latencies[operation] = []
            self._operation_latencies[operation].append(latency)

    def get_statistics(self) -> Dict[str, Any]:
        """Get all collected statistics."""
        with self._lock:
            stats = {
                "io": {
                    "bytes_read_total": self._io_stats.bytes_read_total,
                    "read_operations": self._io_stats.read_operations,
                    "read_speed_mbps": self._io_stats.read_speed_mbps,
                    "avg_read_latency": self._io_stats.avg_read_latency
                },
                "cache": {
                    "hits": self._cache_stats.hits,
                    "misses": self._cache_stats.misses,
                    "hit_ratio": self._cache_stats.hit_ratio
                },
                "operations": {
                    op: {
                        "count": len(latencies),
                        "avg_latency": sum(latencies) / len(latencies) if latencies else 0.0,
                        "min_latency": min(latencies) if latencies else 0.0,
                        "max_latency": max(latencies) if latencies else 0.0
                    }
                    for op, latencies in self._operation_latencies.items()
                }
            }
            return stats

    def reset_statistics(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self._io_stats = IOStats()
            self._cache_stats = CacheStats()
            self._operation_latencies.clear()
            
    def record_metric(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a custom metric.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            metadata: Optional metadata associated with the metric
        """
        with self._lock:
            if name not in self._operation_latencies:
                self._operation_latencies[name] = []
            self._operation_latencies[name].append(value)