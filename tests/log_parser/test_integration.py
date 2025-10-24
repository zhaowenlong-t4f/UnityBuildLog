"""集成测试模块，用于测试各组件之间的协同工作。"""

import unittest
import tempfile
import os
import threading
import time
import gzip
import json
from pathlib import Path
from typing import Dict, Any, Optional

from .utils import TestTimeout
from .utils import TestFileManager

from src.log_parser.reader.base import ReaderContext
from src.log_parser.reader.file_handlers.text_handler import TextFileHandler
from src.log_parser.reader.file_handlers.gzip_handler import GzipFileHandler
from src.log_parser.reader.iterators.chunk_iterator import ChunkIterator
from src.log_parser.reader.iterators.line_iterator import LineIterator
from src.log_parser.reader.cache.cache_manager import CacheManager
from src.log_parser.reader.cache.strategies import LRUCache
from src.config.log_parser.config_manager import ConfigManager

class TestIntegrationFlow(unittest.TestCase):
    """测试完整的日志读取流程。"""
    
    def setUp(self):
        """测试准备工作。"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = Path(self.temp_dir) / "test_log.txt"
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.test_content = "Line 1: Info\nLine 2: Warning\nLine 3: Error\n"
        
        # 初始化测试资源
        self.handler: Optional[TextFileHandler] = None
        self.iterator: Optional[LineIterator] = None
        self.cache_manager: Optional[CacheManager] = None
        
        # 写入测试日志内容
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.test_content)
        
        # 验证文件存在且可读
        self.assertTrue(self.test_file_path.exists(), "测试文件未创建成功")
        self.assertTrue(os.access(self.test_file_path, os.R_OK), "测试文件不可读")
            
        # 初始化配置管理器（禁用文件监控以避免测试干扰）
        self.config_manager = ConfigManager(self.config_path, enable_watch=False)
        
    def tearDown(self):
        """清理测试环境。"""
        # 清理资源
        if self.handler is not None:
            try:
                self.handler.close()
            except:
                pass
        
        if self.iterator is not None:
            try:
                self.iterator.reset()
            except:
                pass
        
        # 清理临时文件
        try:
            if os.path.exists(self.test_file_path):
                os.remove(self.test_file_path)
            if os.path.exists(self.config_path):
                os.remove(self.config_path)
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except:
            pass  # 忽略清理错误
            
    @TestTimeout(5)
    def test_complete_read_workflow(self):
        """测试完整的读取工作流程。"""
        print("\n=== 开始完整读取工作流程测试 ===")
        
        try:
            # 1. 创建并打开文件处理器
            print("创建文件处理器...")
            self.handler = TextFileHandler(self.test_file_path)
            print("打开文件...")
            self.handler.open()
            print("文件处理器准备完成")
            
            # 2. 创建迭代器
            print("创建行迭代器...")
            self.iterator = LineIterator(self.handler)
            print("迭代器创建成功")
            
            # 3. 读取并验证内容
            print("开始读取文件内容...")
            lines = []
            for i, line in enumerate(self.iterator, 1):
                print(f"读取第 {i} 行: {line}")
                lines.append(line)
            
            print(f"共读取到 {len(lines)} 行")
            self.assertEqual(len(lines), 3, "行数不匹配")
            
            # 4. 验证内容
            expected_lines = [
                "Line 1: Info\n",
                "Line 2: Warning\n",
                "Line 3: Error\n"
            ]
            for i, (actual, expected) in enumerate(zip(lines, expected_lines), 1):
                self.assertEqual(actual.replace('\r\n', '\n'), expected, f"第 {i} 行内容不匹配")
                print(f"第 {i} 行验证通过")
            
            print("所有内容验证通过")
            
        except Exception as e:
            print(f"测试过程中发生异常: {e}")
            raise
            
        print("=== 完整读取工作流程测试完成 ===\n")
        
    @TestTimeout(5)
    @TestTimeout(10)
    def test_caching_integration(self):
        """测试缓存系统集成。"""
        print("\n=== 开始缓存系统集成测试 ===")
        
        # 1. 初始化组件
        print("初始化组件...")
        lru_strategy = LRUCache()
        cache_manager = CacheManager(strategy=lru_strategy)
        self.assertIsNotNone(cache_manager)        # 设置较小的缓存大小以便测试
        cache_manager.set_max_size(1024)
        
        # 2. 创建测试数据
        test_files = []
        test_contents = []
        
        print("创建测试文件...")
        for i in range(3):
            content = f"Test file {i} content\n" * 10
            test_contents.append(content)
            
            file_path = Path(self.temp_dir) / f"test_{i}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            test_files.append(file_path)
            print(f"创建文件: {file_path}")
            
        # 3. 测试缓存命中和未命中
        print("\n测试缓存机制...")
        handlers = []
        for file_path in test_files:
            handler = TextFileHandler(file_path)
            handler.open()
            handlers.append(handler)
            
        # 第一轮读取（缓存未命中）
        print("第一轮读取（预期缓存未命中）...")
        first_round_data = []
        for handler in handlers:
            data = handler.read()
            cache_manager.put(str(handler.path), data)
            first_round_data.append(data)
            
        # 验证缓存统计
        stats = cache_manager.get_stats()
        print(f"缓存统计: {stats}")
        self.assertEqual(stats["misses"], len(handlers), "第一轮应该全部未命中")
        
        # 第二轮读取（缓存命中）
        print("\n第二轮读取（预期缓存命中）...")
        for i, handler in enumerate(handlers):
            cached_data = cache_manager.get(str(handler.path))
            self.assertIsNotNone(cached_data, f"文件 {i} 应该在缓存中")
            self.assertEqual(cached_data, first_round_data[i], "缓存数据应该匹配")
            
        # 验证缓存命中
        stats = cache_manager.get_stats()
        print(f"更新后的缓存统计: {stats}")
        self.assertTrue(stats["hits"] >= len(handlers), "第二轮应该有缓存命中")
        
        # 4. 测试缓存淘汰
        print("\n测试缓存淘汰...")
        # 添加更多数据触发淘汰
        extra_data = b"Extra data" * 100
        for i in range(10):
            cache_manager.put(f"extra_key_{i}", extra_data)
            
        # 验证早期数据被淘汰
        evicted = False
        for handler in handlers:
            if cache_manager.get(str(handler.path)) is None:
                evicted = True
                break
        self.assertTrue(evicted, "应该有数据被淘汰")
        
        # 清理
        print("\n清理资源...")
        for handler in handlers:
            handler.close()
        for file_path in test_files:
            os.remove(file_path)
            
        print("=== 缓存系统集成测试完成 ===\n")
        
    @TestTimeout(10)
    def test_component_cooperation(self):
        """测试多组件协同工作。"""
        print("\n=== 开始多组件协同工作测试 ===")
        
        try:
            # 1. 初始化组件
            print("初始化组件...")
            context = ReaderContext(self.test_file_path)
            self.cache_manager = CacheManager(strategy=LRUCache())
            print("组件初始化完成")
            
            # 2. 创建并配置处理器
            print("创建文件处理器...")
            self.handler = TextFileHandler(context)
            self.handler.set_cache_manager(self.cache_manager)
            self.handler.open()
            print("文件处理器准备就绪")
            
            # 3. 创建迭代器并配置
            print("创建迭代器...")
            chunk_iterator = ChunkIterator(self.handler, chunk_size=16)
            line_iterator = LineIterator(self.handler)
            print("迭代器创建完成")
            
            # 4. 先缓存文件内容
            print("\n读取并缓存文件内容...")
            content = self.handler.read()
            print(f"读取了 {len(content)} 字节的数据")
            
            # 重置文件指针
            print("重置文件指针...")
            self.handler.seek(0)
            
            # 5. 测试行读取
            print("\n测试行读取...")
            lines = list(line_iterator)
            print(f"读取到 {len(lines)} 行")
            self.assertEqual(len(lines), 3, "行数不匹配")
            print("行读取验证通过")
            
            # 重置文件指针
            print("重置文件指针...")
            self.handler.seek(0)
            
            # 6. 测试分片读取
            print("\n测试分片读取...")
            chunks = list(chunk_iterator)
            print(f"读取到 {len(chunks)} 个数据块")
            self.assertTrue(len(chunks) > 0, "没有读取到任何数据")
            
            # 重建原始内容进行验证
            chunk_content = ''.join(chunks)
            self.assertEqual(chunk_content, self.test_content)
            print("分片数据验证通过")
            print("行数据验证通过")
            
            # 7. 验证缓存效果
            print("\n验证缓存效果...")
            cached_data = self.cache_manager.get(str(self.test_file_path))
            print(f"缓存数据: {cached_data}")
            self.assertIsNotNone(cached_data, "数据应该被缓存")
            self.assertEqual(cached_data, self.test_content)
            print("缓存验证通过")
            
        except Exception as e:
            print(f"测试过程中发生异常: {e}")
            raise
            
        print("=== 多组件协同工作测试完成 ===\n")
        
    @TestTimeout(10)
    def test_error_handling_and_recovery(self):
        """测试错误处理和恢复机制。"""
        print("\n=== 开始错误处理和恢复测试 ===")
        
        # 1. 文件不存在的情况
        print("\n测试文件不存在场景...")
        invalid_path = Path(self.temp_dir) / "non_existent.txt"
        try:
            TextFileHandler(invalid_path)
            self.fail("应该抛出 FileNotFoundError")
        except FileNotFoundError as e:
            print(f"正确捕获到文件不存在异常: {e}")
        
        # 2. 文件损坏的情况
        print("\n测试文件损坏场景...")
        corrupt_file = Path(self.temp_dir) / "corrupt.gz"
        with open(corrupt_file, "wb") as f:
            f.write(b"This is not a valid gzip file")
        
        try:
            handler = GzipFileHandler(corrupt_file)
            handler.open()
            handler.read()
            self.fail("应该抛出解压错误")
        except Exception as e:
            print(f"正确捕获到文件损坏异常: {e}")
            
        # 3. 权限问题（非Windows系统）
        if os.name != 'nt':
            print("\n测试权限问题场景...")
            try:
                os.chmod(self.test_file_path, 0o000)
                handler = TextFileHandler(self.test_file_path)
                handler.open()
                self.fail("应该抛出权限错误")
            except PermissionError as e:
                print(f"正确捕获到权限错误: {e}")
            finally:
                os.chmod(self.test_file_path, 0o666)
                
        # 4. 恢复机制测试
        print("\n测试文件读取恢复机制...")
        # 创建一个大文件用于测试
        large_file = Path(self.temp_dir) / "large.txt"
        with open(large_file, "w", encoding="utf-8") as f:
            for i in range(1000):
                f.write(f"Line {i}: {'*' * 100}\n")
                
        # 测试分块读取和恢复
        handler = TextFileHandler(large_file)
        handler.open()
        iterator = ChunkIterator(handler, chunk_size=1024)
        
        chunks = []
        retries = 3
        current_pos = 0
        
        for _ in range(retries):
            try:
                for chunk in iterator:
                    chunks.append(chunk)
                    current_pos = handler.tell()
                    if len(chunks) == 5:  # 模拟在读取一定数量后发生错误
                        raise IOError("模拟IO错误")
                break  # 如果没有异常，跳出重试循环
            except IOError as e:
                print(f"捕获到IO错误: {e}")
                print(f"当前位置: {current_pos}")
                print("尝试恢复...")
                handler.seek(current_pos)  # 恢复到最后的有效位置
                continue
                
        self.assertTrue(len(chunks) > 0, "应该至少读取到一些数据")
        print(f"成功读取了 {len(chunks)} 个数据块")
        
        handler.close()
        os.remove(large_file)
        
        print("=== 错误处理和恢复测试完成 ===\n")
        
    @TestTimeout(10)
    def test_config_change_response(self):
        """测试配置变更响应。"""
        print("\n=== 开始配置变更响应测试 ===")
        
        # 1. 初始化配置
        print("创建初始配置...")
        initial_config = {
            "reader": {
                "chunk_size": 4096,
                "buffer_size": 1024,
                "encoding": "utf-8",
                "performance": {
                    "enable_caching": True,
                    "cache_size": 8192
                }
            }
        }
        
        # 创建配置文件
        print("保存初始配置...")
        config_file = Path(self.temp_dir) / "reader_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(initial_config, f, indent=4)
            
        # 2. 创建配置管理器和监听器
        print("初始化配置管理器...")
        config_manager = ConfigManager(config_file, enable_watch=True)
        
        # 跟踪配置变更
        config_changes = []
        def config_callback(new_config):
            config_changes.append(new_config.copy())
            print("配置已更新")
            
        config_manager.register_callback(config_callback)
        
        # 3. 创建并启动组件
        print("创建读取组件...")
        context = ReaderContext(self.test_file_path)
        handler = TextFileHandler(context)
        cache_manager = CacheManager(strategy=LRUCache())
        
        # 4. 测试配置变更
        print("\n更新配置并测试响应...")
        
        # 更改缓冲区大小
        new_config = config_manager.get_config()
        new_config["reader"]["buffer_size"] = 2048
        new_config["reader"]["performance"]["cache_size"] = 16384
        
        print("应用新配置...")
        config_manager.update_config(new_config)
        time.sleep(0.1)  # 等待配置更新传播
        
        # 验证回调被触发
        self.assertTrue(len(config_changes) > 0, "配置变更回调未被触发")
        
        # 验证配置已更新
        current_config = config_manager.get_config()
        self.assertEqual(current_config["reader"]["buffer_size"], 2048)
        self.assertEqual(current_config["reader"]["performance"]["cache_size"], 16384)
        
        # 测试组件响应
        print("测试组件响应...")
        context.update_from_config(current_config["reader"])
        self.assertEqual(context.buffer_size, 2048)
        
        # 测试新配置下的读取操作
        handler.open()
        content = handler.read(1024)
        self.assertIsNotNone(content)
        handler.close()
        
        # 5. 测试配置回滚
        print("\n测试配置回滚...")
        try:
            invalid_config = {"reader": {"buffer_size": -1}}  # 无效配置
            config_manager.update_config(invalid_config)
            self.fail("应该因为无效配置而失败")
        except ValueError as e:
            print(f"正确捕获到配置验证错误: {e}")
            # 验证配置未被破坏
            current_config = config_manager.get_config()
            self.assertEqual(current_config["reader"]["buffer_size"], 2048)
            
        # 清理
        config_manager.stop_watch()
        print("=== 配置变更响应测试完成 ===\n")

if __name__ == '__main__':
    unittest.main()