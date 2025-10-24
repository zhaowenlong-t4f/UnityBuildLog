"""性能测试模块。

此模块包含关键性能指标测试：
1. 读取性能（吞吐量）
2. 缓存性能
3. 并发性能
"""

import unittest
import tempfile
import os
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any
import psutil
import json

from src.log_parser.reader.file_handlers.text_handler import TextFileHandler
from src.log_parser.reader.file_handlers.gzip_handler import GzipFileHandler
from src.log_parser.reader.iterators.line_iterator import LineIterator
from src.log_parser.reader.cache.cache_manager import CacheManager
from src.log_parser.reader.cache.strategies import LRUCache

def generate_large_file(path: Path, size_mb: int = 100) -> None:
    """生成指定大小的测试文件。
    
    Args:
        path: 文件路径
        size_mb: 目标文件大小（MB）
    """
    chunk_size = 1024 * 1024  # 1MB
    template = "This is a test line with random number: {}\n"
    
    with open(path, 'w') as f:
        written = 0
        while written < size_mb * chunk_size:
            line = template.format(random.randint(1, 1000000))
            content = line * (chunk_size // len(line))
            f.write(content)
            written += len(content.encode())

class PerformanceMetrics:
    """性能指标收集器。"""
    
    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        self.start_memory = 0
        self.peak_memory = 0
        self.cpu_usage = []
        self._process = psutil.Process()
        
    def start(self):
        """开始收集指标。"""
        self.start_time = time.time()
        self.start_memory = self._process.memory_info().rss
        self.peak_memory = self.start_memory
        self.cpu_usage = []
        
    def update(self):
        """更新指标。"""
        current_memory = self._process.memory_info().rss
        self.peak_memory = max(self.peak_memory, current_memory)
        self.cpu_usage.append(self._process.cpu_percent())
        
    def stop(self):
        """停止收集指标。"""
        self.end_time = time.time()
        
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标。"""
        duration = self.end_time - self.start_time
        memory_increase = self.peak_memory - self.start_memory
        avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
        
        return {
            "duration": round(duration, 3),
            "memory_increase_mb": round(memory_increase / (1024 * 1024), 2),
            "peak_memory_mb": round(self.peak_memory / (1024 * 1024), 2),
            "avg_cpu_percent": round(avg_cpu, 2)
        }

class TestPerformance(unittest.TestCase):
    """性能测试类。"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化。"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.large_file = Path(cls.temp_dir) / "large_file.txt"
        cls.metrics_file = Path(cls.temp_dir) / "performance_metrics.json"
        
        print("\n=== 生成测试文件 ===")
        print(f"创建 {cls.large_file}")
        generate_large_file(cls.large_file, size_mb=100)  # 生成100MB的测试文件
        print("测试文件生成完成")
        
        # 保存历史指标
        if cls.metrics_file.exists():
            with open(cls.metrics_file, 'r') as f:
                cls.historical_metrics = json.load(f)
        else:
            cls.historical_metrics = {}
            
    @classmethod
    def tearDownClass(cls):
        """测试类清理。"""
        try:
            # 首先保存性能指标
            with open(cls.metrics_file, 'w') as f:
                json.dump(cls.historical_metrics, f, indent=2)
                
            # 然后清理文件
            os.remove(cls.large_file)
            os.rmdir(cls.temp_dir)
        except Exception as e:
            print(f"清理时发生错误: {e}")
            pass
            
    def setUp(self):
        """测试准备。"""
        self.metrics = PerformanceMetrics()
        
    def test_read_throughput(self):
        """测试读取吞吐量。"""
        print("\n=== 开始读取吞吐量测试 ===")
        
        # 1. 大块读取测试
        self.metrics.start()
        handler = TextFileHandler(self.large_file)
        handler.open()
        
        chunk_sizes = [1024, 1024*1024, 1024*1024*10]  # 1KB, 1MB, 10MB
        for chunk_size in chunk_sizes:
            print(f"\n测试块大小: {chunk_size/1024:.1f}KB")
            bytes_read = 0
            handler.seek(0)
            
            start = time.time()
            while True:
                data = handler.read(chunk_size)
                if not data:
                    break
                bytes_read += len(data.encode())
                self.metrics.update()
                
            duration = time.time() - start
            throughput = bytes_read / (1024*1024) / duration  # MB/s
            print(f"吞吐量: {throughput:.2f} MB/s")
            
        handler.close()
        self.metrics.stop()
        
        # 保存指标
        metrics = self.metrics.get_metrics()
        print(f"\n性能指标: {json.dumps(metrics, indent=2)}")
        self.historical_metrics["read_throughput"] = metrics
        
    def test_cache_performance(self):
        """测试缓存性能。"""
        print("\n=== 开始缓存性能测试 ===")
        
        cache_manager = CacheManager(strategy=LRUCache())
        handler = TextFileHandler(self.large_file)
        handler.set_cache_manager(cache_manager)
        
        self.metrics.start()
        
        # 1. 首次读取（未缓存）
        print("\n首次读取（未缓存）")
        handler.open()
        start = time.time()
        content = handler.read()
        duration = time.time() - start
        print(f"读取耗时: {duration:.3f}秒")
        
        # 2. 二次读取（已缓存）
        print("\n二次读取（已缓存）")
        handler.seek(0)
        start = time.time()
        cached_content = handler.read()
        duration = time.time() - start
        print(f"读取耗时: {duration:.3f}秒")
        
        # 3. 验证缓存效果
        stats = cache_manager.get_stats()
        print(f"\n缓存统计: {stats}")
        
        handler.close()
        self.metrics.stop()
        
        # 保存指标
        metrics = self.metrics.get_metrics()
        print(f"\n性能指标: {json.dumps(metrics, indent=2)}")
        self.historical_metrics["cache_performance"] = metrics
        
    def test_concurrent_reads(self):
        """测试并发读取性能。"""
        print("\n=== 开始并发读取测试 ===")
        
        def read_file(file_path: Path, offset: int, size: int) -> int:
            """读取文件片段。"""
            handler = TextFileHandler(file_path)
            handler.open()
            handler.seek(offset)
            data = handler.read(size)
            handler.close()
            return len(data.encode() if isinstance(data, str) else data)
            
        # 将文件分成多个块并发读取
        file_size = os.path.getsize(self.large_file)
        num_threads = 4
        chunk_size = file_size // num_threads
        
        self.metrics.start()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                offset = i * chunk_size
                size = chunk_size if i < num_threads - 1 else file_size - offset
                futures.append(executor.submit(read_file, self.large_file, offset, size))
                
            # 等待所有任务完成并收集结果
            total_bytes = 0
            start = time.time()
            for future in futures:
                total_bytes += future.result()
                self.metrics.update()
                
        duration = time.time() - start
        throughput = total_bytes / (1024*1024) / duration  # MB/s
        print(f"\n并发吞吐量: {throughput:.2f} MB/s")
        
        self.metrics.stop()
        
        # 保存指标
        metrics = self.metrics.get_metrics()
        print(f"\n性能指标: {json.dumps(metrics, indent=2)}")
        self.historical_metrics["concurrent_reads"] = metrics

if __name__ == '__main__':
    unittest.main()