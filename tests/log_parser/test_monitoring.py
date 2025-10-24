"""Tests for the monitoring system components."""
import unittest
import time
from src.log_parser.reader.monitoring.stats_collector import StatsCollector
from src.log_parser.reader.monitoring.memory_monitor import MemoryMonitor

class TestStatsCollector(unittest.TestCase):
    """Test cases for StatsCollector."""

    def setUp(self):
        self.stats_collector = StatsCollector()

    def test_io_stats_collection(self):
        """Test IO statistics collection."""
        self.stats_collector.collect_io_stats(1024, 0.1)
        time.sleep(0.1)  # 添加延时确保有足够的经过时间
        self.stats_collector.collect_io_stats(2048, 0.2)
        
        stats = self.stats_collector.get_statistics()
        self.assertEqual(stats['io']['bytes_read_total'], 3072)
        self.assertEqual(stats['io']['read_operations'], 2)
        self.assertGreater(stats['io']['read_speed_mbps'], 0)

    def test_cache_stats_collection(self):
        """Test cache statistics collection."""
        self.stats_collector.collect_cache_stats(True)  # hit
        self.stats_collector.collect_cache_stats(False)  # miss
        self.stats_collector.collect_cache_stats(True)  # hit
        
        stats = self.stats_collector.get_statistics()
        self.assertEqual(stats['cache']['hits'], 2)
        self.assertEqual(stats['cache']['misses'], 1)
        self.assertAlmostEqual(stats['cache']['hit_ratio'], 2/3)

    def test_operation_latency_collection(self):
        """Test operation latency collection."""
        self.stats_collector.collect_operation_latency('read', 0.1)
        self.stats_collector.collect_operation_latency('read', 0.2)
        
        stats = self.stats_collector.get_statistics()
        self.assertEqual(stats['operations']['read']['count'], 2)
        self.assertAlmostEqual(stats['operations']['read']['avg_latency'], 0.15)

class TestMemoryMonitor(unittest.TestCase):
    """Test cases for MemoryMonitor."""

    def setUp(self):
        self.memory_monitor = MemoryMonitor(threshold=0.8, sampling_interval=1.0)

    def test_memory_usage_check(self):
        """Test memory usage monitoring."""
        usage = self.memory_monitor.check_memory_usage()
        self.assertGreaterEqual(usage, 0.0)
        self.assertLessEqual(usage, 1.0)

    def test_garbage_collection_trigger(self):
        """Test garbage collection triggering."""
        # 创建一些内存压力
        large_list = [0] * 1000000
        trigger = self.memory_monitor.should_trigger_gc()
        self.assertIsInstance(trigger, bool)
        del large_list

    def test_memory_trend_monitoring(self):
        """Test memory trend monitoring."""
        self.memory_monitor.start_monitoring()
        time.sleep(2.0)  # 等待几个采样点
        trend = self.memory_monitor.get_memory_trend()
        self.memory_monitor.stop_monitoring()
        
        self.assertGreater(len(trend), 0)
        for point in trend:
            self.assertIn('timestamp', point)
            self.assertIn('used_mb', point)
            self.assertIn('percent', point)

if __name__ == '__main__':
    unittest.main()