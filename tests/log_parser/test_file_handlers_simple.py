"""简化的文件处理器测试模块。"""

import unittest
import tempfile
import os
import threading
import time
from pathlib import Path
from typing import Optional

from src.log_parser.reader.file_handlers.text_handler import TextFileHandler
from src.log_parser.reader.file_handlers.base import BaseFileHandler

class TestTimeout:
    """测试超时装饰器。"""
    
    def __init__(self, seconds: int):
        self.seconds = seconds
        
    def __call__(self, func):
        def wrapped(instance):
            timeout_flag = {'timeout': False}
            
            def target():
                try:
                    func(instance)
                except Exception as e:
                    instance.test_exception = e
                    
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(self.seconds)
            
            if thread.is_alive():
                timeout_flag['timeout'] = True
                raise TimeoutError(f"测试超时（{self.seconds}秒）")
                
            if hasattr(instance, 'test_exception'):
                raise instance.test_exception
                
        return wrapped

class TestTextFileHandler(unittest.TestCase):
    """文件处理器简化测试。"""
    
    def setUp(self):
        """准备测试环境。"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_content = "测试内容"
        self.handler: Optional[TextFileHandler] = None
        
        # 创建测试文件
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
        
        # 验证文件存在且可读
        self.assertTrue(self.test_file.exists(), "测试文件未创建成功")
        self.assertTrue(os.access(self.test_file, os.R_OK), "测试文件不可读")
        
    def tearDown(self):
        """清理测试环境。"""
        # 确保关闭文件
        if self.handler is not None:
            try:
                self.handler.close()
            except:
                pass
                
        # 清理文件
        try:
            if self.test_file.exists():
                os.remove(self.test_file)
            os.rmdir(self.temp_dir)
        except:
            pass
            
    @TestTimeout(5)
    def test_basic_read(self):
        """测试基本的文件读取功能。"""
        print("\n=== 开始基本读取测试 ===")
        
        # 1. 创建处理器
        print("创建文件处理器...")
        self.handler = TextFileHandler(self.test_file)
        print("文件处理器创建成功")
        
        # 2. 打开文件
        print("打开文件...")
        self.handler.open()
        print("文件打开成功")
        
        # 3. 读取内容
        print("读取文件内容...")
        data = self.handler.read()
        print(f"读取到内容: {data}")
        
        # 4. 验证内容
        self.assertEqual(data.decode('utf-8'), self.test_content)
        print("内容验证通过")
        
        print("=== 基本读取测试完成 ===")
        
    @TestTimeout(5)
    def test_file_not_found(self):
        """测试文件不存在的情况。"""
        print("\n=== 开始文件不存在测试 ===")
        
        # 1. 准备不存在的文件路径
        non_existent = Path(self.temp_dir) / "not_exist.txt"
        print(f"创建不存在的文件路径: {non_existent}")
        
        # 2. 验证文件确实不存在
        self.assertFalse(non_existent.exists())
        print("确认文件不存在")
        
        # 3. 尝试创建处理器
        print("尝试创建文件处理器...")
        with self.assertRaises(FileNotFoundError) as context:
            TextFileHandler(non_existent)
        print(f"成功捕获到异常: {context.exception}")
        
        print("=== 文件不存在测试完成 ===")
        
    @TestTimeout(5)
    def test_read_permissions(self):
        """测试文件权限问题。"""
        print("\n=== 开始文件权限测试 ===")
        
        if os.name != 'nt':  # 跳过Windows系统
            # 1. 移除读取权限
            print("移除文件读取权限...")
            os.chmod(self.test_file, 0o000)
            
            # 2. 尝试创建处理器
            print("尝试创建文件处理器...")
            with self.assertRaises(PermissionError):
                TextFileHandler(self.test_file)
            print("成功捕获到权限错误")
            
            # 恢复权限
            os.chmod(self.test_file, 0o666)
            
        print("=== 文件权限测试完成 ===")

if __name__ == '__main__':
    unittest.main()