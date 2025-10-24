"""
缓存监控实现
"""
from typing import Dict, Any
import time

class CacheMonitor:
    """缓存监控器"""
    
    def __init__(self):
        self._start_time = time.time()
        self._stats: Dict[str, Any] = {
            "total_operations": 0,
            "hit_rate": 0.0,
            "miss_rate": 0.0,
            "eviction_rate": 0.0,
            "average_get_time": 0.0,
            "total_get_time": 0.0
        }
        
    def record_operation(self, operation_type: str, duration: float) -> None:
        """记录缓存操作
        
        Args:
            operation_type: 操作类型(get/put/remove)
            duration: 操作耗时
        """
        self._stats["total_operations"] += 1
        if operation_type == "get":
            self._stats["total_get_time"] += duration
            self._stats["average_get_time"] = (
                self._stats["total_get_time"] / self._stats["total_operations"]
            )
            
    def update_rates(self, hits: int, misses: int, evictions: int) -> None:
        """更新缓存命中率等统计信息
        
        Args:
            hits: 命中次数
            misses: 未命中次数
            evictions: 淘汰次数
        """
        total = hits + misses
        if total > 0:
            self._stats["hit_rate"] = hits / total
            self._stats["miss_rate"] = misses / total
        if self._stats["total_operations"] > 0:
            self._stats["eviction_rate"] = evictions / self._stats["total_operations"]
            
    def get_stats(self) -> Dict[str, Any]:
        """获取监控统计信息
        
        Returns:
            包含各项统计指标的字典
        """
        return self._stats.copy()
        
    def reset(self) -> None:
        """重置统计信息"""
        self._start_time = time.time()
        for key in self._stats:
            if isinstance(self._stats[key], float):
                self._stats[key] = 0.0
            else:
                self._stats[key] = 0