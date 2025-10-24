"""基础内存泄漏测试模块。

此模块包含基本的内存泄漏测试，主要测试：
1. 资源正确释放
2. 循环读取操作
3. 大量实例创建和销毁
"""

import unittest
import tempfile
import os
import gc
import time
from pathlib import Path
from typing import List, Set

from src.log_parser.reader.file_handlers.text_handler import TextFileHandler
from src.log_parser.reader.iterators.line_iterator import LineIterator
from src.log_parser.reader.cache.cache_manager import CacheManager
from src.log_parser.reader.cache.strategies import LRUCache

class TestMemoryLeak(unittest.TestCase):
    """基本内存泄漏测试类。"""
    
    def setUp(self):
        """测试准备工作。"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files: List[Path] = []
        self.handlers: List[TextFileHandler] = []
        
        # 创建测试文件
        for i in range(5):
            file_path = Path(self.temp_dir) / f"test_{i}.txt"
            content = f"Test file {i} content\n" * 1000  # 每个文件约20KB
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.test_files.append(file_path)
            
    def tearDown(self):
        """清理测试环境。"""
        # 确保所有处理器都被关闭
        for handler in self.handlers:
            try:
                handler.close()
            except:
                pass
                
        # 清理文件
        for file_path in self.test_files:
            try:
                os.remove(file_path)
            except:
                pass
                
        # 清理临时目录
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
            
        # 手动触发垃圾回收
        gc.collect()
        
    def test_handler_resource_release(self):
        """测试文件处理器资源释放。"""
        print("\n=== 开始处理器资源释放测试 ===")
        active_handlers: Set[int] = set()
        
        for i in range(100):  # 创建100个处理器实例
            handler = TextFileHandler(self.test_files[i % len(self.test_files)])
            handler_id = id(handler)
            active_handlers.add(handler_id)
            
            # 打开文件
            handler.open()
            # 读取一些数据
            _ = handler.read(1024)
            # 确保正确关闭
            handler.close()
            
            # 删除引用
            del handler
            
            # 每10次操作检查一次活跃的处理器数量
            if i > 0 and i % 10 == 0:
                # 触发垃圾回收
                gc.collect()
                
                # 获取当前存活的处理器数量
                current_handlers = set([id(obj) for obj in gc.get_objects() 
                                     if isinstance(obj, TextFileHandler)])
                                     
                # 计算仍然存活的旧处理器数量
                surviving = len(active_handlers.intersection(current_handlers))
                print(f"第 {i} 次迭代，存活的旧处理器数量: {surviving}")
                
                # 确认大部分旧处理器已被回收
                self.assertLess(surviving, 5, 
                              f"发现 {surviving} 个未释放的处理器实例")
                              
                # 更新活跃处理器集合
                active_handlers = current_handlers
                
        print("处理器资源释放测试完成")
        
    def test_iterator_resource_management(self):
        """测试迭代器资源管理。"""
        print("\n=== 开始迭代器资源管理测试 ===")
        
        for i in range(50):  # 进行50次迭代测试
            # 创建处理器和迭代器
            handler = TextFileHandler(self.test_files[i % len(self.test_files)])
            handler.open()
            iterator = LineIterator(handler)
            
            # 记录初始内存使用
            gc.collect()
            
            # 部分读取（模拟中断操作）
            lines_read = 0
            for line in iterator:
                lines_read += 1
                if lines_read >= 500:  # 只读取前500行
                    break
                    
            # 确保资源正确释放
            handler.close()
            del iterator
            del handler
            
            # 强制垃圾回收
            gc.collect()
            
            print(f"完成第 {i+1} 次迭代器测试")
            
        print("迭代器资源管理测试完成")
        
    def test_cache_memory_management(self):
        """测试缓存内存管理。"""
        print("\n=== 开始缓存内存管理测试 ===")
        
        # 创建一个较小的缓存来测试淘汰机制
        cache_manager = CacheManager(strategy=LRUCache(), max_size=1024 * 50)  # 50KB
        
        for i in range(30):  # 30次循环，每次都会触发缓存淘汰
            print(f"\n第 {i+1} 次缓存测试循环")
            
            # 读取所有测试文件
            for file_path in self.test_files:
                handler = TextFileHandler(file_path)
                handler.set_cache_manager(cache_manager)
                handler.open()
                
                # 读取文件内容
                content = handler.read()
                handler.close()
                
                # 验证缓存状态
                stats = cache_manager.get_stats()
                print(f"缓存统计: {stats}")
                
                # 确保缓存大小在限制范围内
                self.assertLessEqual(
                    stats["current_size"], 
                    stats["max_size"],
                    "缓存大小超出限制"
                )
                
                # 清理
                del handler
                
            # 每轮结束后进行垃圾回收
            gc.collect()
            
        print("缓存内存管理测试完成")

if __name__ == '__main__':
    unittest.main()