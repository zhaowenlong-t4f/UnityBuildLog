"""Tests for the log reader module."""

import os
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.log_parser.reader.base import ReaderContext, ReadResult
from src.log_parser.reader.file_handlers.text_handler import TextFileHandler
from src.log_parser.reader.exceptions import ReadError

class TestLogReader(unittest.TestCase):
    """Test cases for the log reader module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # 创建临时测试文件
        self.test_content = "Hello\nWorld\n这是一个测试文件".encode('utf-8')
        self.temp_file = NamedTemporaryFile(delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.file_path = Path(self.temp_file.name)
        
    def tearDown(self):
        """Tear down test fixtures."""
        # 删除临时文件
        if os.path.exists(self.file_path):
            os.unlink(self.file_path)
    
    def test_reader_context(self):
        """Test ReaderContext functionality."""
        context = ReaderContext(self.file_path)
        self.assertEqual(context.file_path, self.file_path)
        self.assertEqual(context.encoding, 'utf-8')
        self.assertEqual(context.position, 0)
        
        # 测试元数据操作
        context.add_metadata('test_key', 'test_value')
        self.assertEqual(context.get_metadata('test_key'), 'test_value')
        self.assertEqual(context.get_metadata('non_existent', 'default'), 'default')
        
        # 测试重置
        context.position = 100
        context.reset()
        self.assertEqual(context.position, 0)
        self.assertEqual(context.metadata, {})
    
    def test_text_file_handler(self):
        """Test TextFileHandler functionality."""
        handler = TextFileHandler(self.file_path)
        
        # 测试打开文件
        handler.open()
        self.assertTrue(handler._is_open)
        
        # 测试读取内容
        content = handler.read()
        self.assertEqual(content, self.test_content)
        
        # 测试seek和tell
        handler.seek(0)
        self.assertEqual(handler.tell(), 0)
        
        # 测试按大小读取
        chunk = handler.read(5)
        self.assertEqual(chunk, self.test_content[:5])
        
        # 测试获取元数据
        metadata = handler.get_metadata()
        self.assertEqual(metadata['encoding'], 'utf-8')
        self.assertEqual(metadata['file_type'], 'text')
        
        # 测试关闭文件
        handler.close()
        self.assertFalse(handler._is_open)
        
        # 测试错误处理
        with self.assertRaises(OSError):
            handler.read()
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        # 测试不存在的文件
        with self.assertRaises(FileNotFoundError):
            handler = TextFileHandler(Path('non_existent_file.txt'))
            handler.open()
        
        # 测试无效的编码
        with self.assertRaises(LookupError):
            TextFileHandler(self.file_path, encoding='invalid_encoding')
        
        # 测试无效的size参数
        handler = TextFileHandler(self.file_path)
        handler.open()
        with self.assertRaises(ValueError):
            handler.read(-2)
        handler.close()