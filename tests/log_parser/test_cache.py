"""
缓存系统单元测试
"""
import unittest
import time
from src.log_parser.reader.cache import CacheManager, LRUCache, TTLCache

class TestLRUCache(unittest.TestCase):
    """测试LRU缓存策略"""
    
    def setUp(self):
        """测试前初始化"""
        self.cache = LRUCache()
        
    def test_basic_operations(self):
        """测试基本操作"""
        # 测试存取
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertIsNone(self.cache.get("nonexistent"))
        
        # 测试删除
        self.cache.remove("key1")
        self.assertIsNone(self.cache.get("key1"))
        
        # 测试清空
        self.cache.put("key2", "value2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key2"))
        
    def test_lru_eviction(self):
        """测试LRU淘汰机制"""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.get("key1")  # 访问key1，使其成为最近使用
        
        # 获取最近最少使用的键
        lru_key = self.cache.get_least_recently_used()
        self.assertEqual(lru_key, "key2")
        
class TestTTLCache(unittest.TestCase):
    """测试TTL缓存策略"""
    
    def setUp(self):
        """测试前初始化"""
        self.cache = TTLCache(ttl=1)  # 设置1秒过期时间用于测试
        
    def test_expiration(self):
        """测试过期机制"""
        # 添加缓存项
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # 等待过期
        time.sleep(1.1)
        self.assertIsNone(self.cache.get("key1"))
        
    def test_size_with_expiration(self):
        """测试带过期的大小计算"""
        self.cache.put("key1", "value1")
        initial_size = self.cache.get_size()
        
        # 等待过期
        time.sleep(1.1)
        # get_size应该触发过期清理
        self.assertTrue(self.cache.get_size() < initial_size)

class TestCacheManager(unittest.TestCase):
    """测试缓存管理器"""
    
    def setUp(self):
        """测试前初始化"""
        self.strategy = LRUCache()
        self.manager = CacheManager(strategy=self.strategy, max_size=100)
        
    def test_cache_stats(self):
        """测试缓存统计"""
        # 测试命中统计
        self.manager.put("key1", "value1")
        self.manager.get("key1")  # 命中
        self.manager.get("nonexistent")  # 未命中
        
        stats = self.manager.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        
    def test_size_limit(self):
        """测试大小限制"""
        # 添加超过限制的数据应该触发淘汰
        large_value = "x" * 90  # 90字节的数据
        self.manager.put("key1", large_value)
        self.manager.put("key2", large_value)  # 应该触发淘汰
        
        stats = self.manager.get_stats()
        self.assertTrue(stats["evictions"] > 0)
        self.assertIsNone(self.manager.get("key1"))  # key1应该被淘汰

if __name__ == '__main__':
    unittest.main()