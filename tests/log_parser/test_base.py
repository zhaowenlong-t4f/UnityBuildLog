"""基础类测试。"""

import unittest
from pathlib import Path
from typing import Dict, Any

from src.log_parser.reader.base import ReadResult, ReaderContext

class TestReadResult(unittest.TestCase):
    """ReadResult类的测试用例。"""
    
    def setUp(self):
        """测试准备。"""
        self.test_content = b"test content"
        self.test_position = 42
        self.test_size = len(self.test_content)
        self.test_metadata = {"encoding": "utf-8"}
        
    def test_creation(self):
        """测试ReadResult的创建。"""
        result = ReadResult(
            content=self.test_content,
            position=self.test_position,
            size=self.test_size,
            is_eof=False,
            metadata=self.test_metadata
        )
        
        self.assertEqual(result.content, self.test_content)
        self.assertEqual(result.position, self.test_position)
        self.assertEqual(result.size, self.test_size)
        self.assertFalse(result.is_eof)
        self.assertEqual(result.metadata, self.test_metadata)
        
    def test_empty_metadata(self):
        """测试空元数据的情况。"""
        result = ReadResult(
            content=self.test_content,
            position=self.test_position,
            size=self.test_size,
            is_eof=True,
            metadata={}
        )
        
        self.assertEqual(result.metadata, {})

class TestReaderContext(unittest.TestCase):
    """ReaderContext类的测试用例。"""
    
    def setUp(self):
        """测试准备。"""
        self.test_path = Path("test.txt")
        self.test_encoding = "utf-8"
        self.test_buffer_size = 4096
        self.test_chunk_size = 8 * 1024 * 1024
        
    def test_creation(self):
        """测试ReaderContext的创建。"""
        context = ReaderContext(
            file_path=self.test_path,
            encoding=self.test_encoding,
            buffer_size=self.test_buffer_size,
            chunk_size=self.test_chunk_size
        )
        
        self.assertEqual(context.file_path, self.test_path)
        self.assertEqual(context.encoding, self.test_encoding)
        self.assertEqual(context.buffer_size, self.test_buffer_size)
        self.assertEqual(context.chunk_size, self.test_chunk_size)
        self.assertEqual(context.position, 0)
        self.assertEqual(context.total_bytes_read, 0)
        self.assertFalse(context.is_closed)
        
    def test_metadata_management(self):
        """测试元数据管理功能。"""
        context = ReaderContext(self.test_path)
        
        # 测试添加元数据
        context.add_metadata("key1", "value1")
        context.add_metadata("key2", 42)
        
        self.assertEqual(context.get_metadata("key1"), "value1")
        self.assertEqual(context.get_metadata("key2"), 42)
        self.assertEqual(context.get_metadata("non_existent", "default"), "default")
        
    def test_reset(self):
        """测试重置功能。"""
        context = ReaderContext(self.test_path)
        
        # 设置一些状态
        context.position = 100
        context.total_bytes_read = 200
        context.is_closed = True
        context.add_metadata("test_key", "test_value")
        
        # 重置状态
        context.reset()
        
        # 验证重置结果
        self.assertEqual(context.position, 0)
        self.assertEqual(context.total_bytes_read, 0)
        self.assertFalse(context.is_closed)
        self.assertEqual(context.metadata, {})
        
    def test_default_values(self):
        """测试默认值。"""
        context = ReaderContext(self.test_path)
        
        self.assertEqual(context.encoding, "utf-8")
        self.assertEqual(context.buffer_size, 8192)
        self.assertEqual(context.chunk_size, 8 * 1024 * 1024)

if __name__ == '__main__':
    unittest.main()