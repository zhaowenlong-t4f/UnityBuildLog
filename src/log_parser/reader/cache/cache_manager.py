"""
缓存管理器实现

提供统一的缓存管理接口,支持多种缓存策略
"""
from typing import Any, Optional, Dict, Union, List
from abc import ABC, abstractmethod
import sys

def calculate_size(obj: Any) -> int:
    """计算对象的内存大小
    
    Args:
        obj: 要计算大小的对象
        
    Returns:
        对象占用的字节数
    """
    if isinstance(obj, (str, bytes)):
        return sys.getsizeof(obj)
    elif isinstance(obj, (list, tuple)):
        return sys.getsizeof(obj) + sum(calculate_size(item) for item in obj)
    elif isinstance(obj, dict):
        return sys.getsizeof(obj) + sum(calculate_size(k) + calculate_size(v) for k, v in obj.items())
    else:
        return sys.getsizeof(obj)

class CacheStrategy(ABC):
    """缓存策略基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        """存储缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        pass
    
    @abstractmethod
    def remove(self, key: str) -> None:
        """删除缓存值
        
        Args:
            key: 要删除的缓存键
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """获取当前缓存大小
        
        Returns:
            当前缓存占用的字节数
        """
        pass
        
    @abstractmethod
    def evict_one(self) -> None:
        """淘汰一个缓存项"""
        pass
        
    @abstractmethod
    def keys(self) -> List[str]:
        """获取所有缓存键
        
        Returns:
            缓存键列表
        """
        pass

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, strategy: CacheStrategy, max_size: int = 100 * 1024 * 1024):
        """初始化缓存管理器
        
        Args:
            strategy: 缓存策略实例
            max_size: 最大缓存大小,默认100MB
        """
        self._strategy = strategy
        self._max_size = max_size
        self._stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def has(self, key: str) -> bool:
        """检查键是否存在于缓存中
        
        Args:
            key: 缓存键
            
        Returns:
            如果键存在于缓存中返回True，否则返回False
        """
        return self._strategy.get(key) is not None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值,不存在则返回None
        """
        value = self._strategy.get(key)
        if value is not None:
            self._stats["hits"] += 1
        return value
    
    def put(self, key: str, value: Any) -> None:
        """存储缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果键不存在，计为未命中
        if not self._strategy.get(key):
            self._stats["misses"] += 1
            
        value_size = calculate_size(value)
        
        # 循环淘汰，直到有足够空间
        while self._strategy.get_size() + value_size > self._max_size:
            # 如果当前完全没有缓存项，且单个值就超过了最大大小，则不缓存
            if not self._strategy.keys():
                return
                
            self._stats["evictions"] += 1
            self._strategy.evict_one()
            
        self._strategy.put(key, value)
    
    def clear(self) -> None:
        """清空缓存"""
        self._strategy.clear()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
    def set_max_size(self, size: int) -> None:
        """设置最大缓存大小
        
        Args:
            size: 新的最大缓存大小（字节）
            
        Raises:
            ValueError: 如果大小小于等于0
        """
        if size <= 0:
            raise ValueError("缓存大小必须大于0")
            
        old_size = self._max_size
        self._max_size = size
        
        # 如果新的大小更小，可能需要淘汰一些项
        if size < old_size:
            while self._strategy.get_size() > size:
                if not self._strategy.keys():
                    break
                self._stats["evictions"] += 1
                self._strategy.evict_one()
                
    def get_max_size(self) -> int:
        """获取最大缓存大小
        
        Returns:
            最大缓存大小（字节）
        """
        return self._max_size
        
    def get_current_size(self) -> int:
        """获取当前缓存大小
        
        Returns:
            当前缓存占用的字节数
        """
        return self._strategy.get_size()
        
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计信息
        
        Returns:
            包含命中数、未命中数、淘汰数及大小信息的字典
        """
        stats = self._stats.copy()
        stats.update({
            "current_size": self.get_current_size(),
            "max_size": self.get_max_size()
        })
        return stats