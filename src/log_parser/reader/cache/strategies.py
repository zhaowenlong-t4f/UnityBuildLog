"""
缓存策略实现

包含LRU和TTL两种缓存策略的实现
"""
from typing import Any, Optional, Dict, List
from collections import OrderedDict
import time
from .cache_manager import CacheStrategy, calculate_size

class LRUCache(CacheStrategy):
    """LRU (Least Recently Used) 缓存策略实现"""
    
    def __init__(self):
        self._cache = OrderedDict()
        self._size = 0
        
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        # 移动到OrderedDict末尾表示最近使用
        value = self._cache.pop(key)
        self._cache[key] = value
        return value
        
    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._size -= calculate_size(self._cache[key])
            del self._cache[key]
        self._cache[key] = value
        self._size += calculate_size(value)
        
    def remove(self, key: str) -> None:
        if key in self._cache:
            self._size -= calculate_size(self._cache[key])
            del self._cache[key]
            
    def clear(self) -> None:
        self._cache.clear()
        self._size = 0
        
    def get_size(self) -> int:
        return self._size
        
    def evict_one(self) -> None:
        """淘汰最近最少使用的缓存项"""
        if self._cache:
            key = next(iter(self._cache))
            self.remove(key)
            
    def keys(self) -> List[str]:
        """获取所有缓存键"""
        return list(self._cache.keys())

class TTLCache(CacheStrategy):
    """TTL (Time To Live) 缓存策略实现"""
    
    def __init__(self, ttl: int = 300):  # 默认5分钟过期
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._size = 0
        self._ttl = ttl
        
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        value, expire_time = self._cache[key]
        if time.time() > expire_time:
            self.remove(key)
            return None
        return value
        
    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._size -= calculate_size(self._cache[key][0])
        expire_time = time.time() + self._ttl
        self._cache[key] = (value, expire_time)
        self._size += calculate_size(value)
        
    def remove(self, key: str) -> None:
        if key in self._cache:
            self._size -= calculate_size(self._cache[key][0])
            del self._cache[key]
            
    def clear(self) -> None:
        self._cache.clear()
        self._size = 0
        
    def get_size(self) -> int:
        # 清理过期数据
        current_time = time.time()
        expired_keys = [
            key for key, (_, expire_time) in self._cache.items()
            if current_time > expire_time
        ]
        for key in expired_keys:
            self.remove(key)
        return self._size
        
    def evict_one(self) -> None:
        """淘汰最早过期的缓存项"""
        if not self._cache:
            return
            
        # 清理已过期的项
        current_time = time.time()
        expired_keys = [
            key for key, (_, expire_time) in self._cache.items()
            if current_time > expire_time
        ]
        
        if expired_keys:
            # 如果有过期的项，删除第一个
            self.remove(expired_keys[0])
            return
            
        # 如果没有过期的项，删除最早过期的
        earliest_key = min(self._cache.items(), key=lambda x: x[1][1])[0]
        self.remove(earliest_key)
        
    def keys(self) -> List[str]:
        """获取所有缓存键"""
        # 清理过期数据并返回剩余的键
        current_time = time.time()
        return [
            key for key, (_, expire_time) in self._cache.items()
            if current_time <= expire_time
        ]