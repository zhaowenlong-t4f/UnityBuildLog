"""测试用的LRU缓存策略实现。"""

from collections import OrderedDict
from typing import Any, Optional, Dict, List
from src.log_parser.reader.cache.cache_manager import CacheStrategy, calculate_size


class LRUTestStrategy(CacheStrategy):
    """测试用的LRU缓存策略。"""
    
    def __init__(self):
        """初始化LRU策略。"""
        self._cache: OrderedDict = OrderedDict()
        self._sizes: Dict[str, int] = {}
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值。
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        if key not in self._cache:
            return None
            
        # 移动到最新位置
        value = self._cache.pop(key)
        self._cache[key] = value
        return value
    
    def put(self, key: str, value: Any) -> None:
        """存储缓存值。
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        if key in self._cache:
            self._cache.pop(key)
            self._sizes.pop(key, None)
            
        self._cache[key] = value
        self._sizes[key] = calculate_size(value)
    
    def remove(self, key: str) -> None:
        """删除缓存值。
        
        Args:
            key: 要删除的缓存键
        """
        if key in self._cache:
            self._cache.pop(key)
            self._sizes.pop(key, None)
    
    def clear(self) -> None:
        """清空缓存。"""
        self._cache.clear()
        self._sizes.clear()
    
    def get_size(self) -> int:
        """获取当前缓存大小。
        
        Returns:
            当前缓存占用的字节数
        """
        return sum(self._sizes.values())
    
    def evict_one(self) -> None:
        """淘汰最旧的缓存项。"""
        if self._cache:
            key, _ = self._cache.popitem(last=False)  # 移除最先加入的项
            self._sizes.pop(key, None)
    
    def keys(self) -> List[str]:
        """获取所有缓存键。
        
        Returns:
            缓存键列表
        """
        return list(self._cache.keys())