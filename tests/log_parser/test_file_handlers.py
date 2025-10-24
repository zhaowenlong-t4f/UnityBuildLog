"""文件处理器测试。"""

import unittest
import gzip
from pathlib import Path
from typing import Dict, Any

from src.log_parser.reader.file_handlers import (
    BaseFileHandler,
    TextFileHandler,
    GzipFileHandler,
    FileHandlerFactory
)
from src.log_parser.reader.exceptions import FileFormatError, ReadError
from tests.log_parser.utils import TestFileManager

class TestBaseFileHandler(unittest.TestCase):
    """基础文件处理器测试。"""
    
    def setUp(self):
        """测试准备。"""
        self.test_manager = TestFileManager()
        self.test_content = b"Hello, World!"
        
    def tearDown(self):
        """测试清理。"""
        self.test_manager.cleanup()
        
    def test_file_operations(self):
        """测试基本文件操作。"""
        with self.test_manager as manager:
            file_path = manager.create_file(self.test_content)
            
            class TestHandler(BaseFileHandler):
                def read(self, size: int = -1) -> bytes:
                    return self._file.read(size)
                    
            handler = TestHandler(file_path)
            
            # 测试打开文件
            self.assertFalse(handler.is_open)
            handler.open()
            self.assertTrue(handler.is_open)
            
            # 测试关闭文件
            handler.close()
            self.assertFalse(handler.is_open)
            
    def test_seek_and_tell(self):
        """测试文件定位操作。"""
        with self.test_manager as manager:
            file_path = manager.create_file(self.test_content)
            
            class TestHandler(BaseFileHandler):
                def read(self, size: int = -1) -> bytes:
                    return self._file.read(size)
                    
            with TestHandler(file_path) as handler:
                handler.open()
                
                # 测试seek和tell
                handler.seek(5)
                self.assertEqual(handler.tell(), 5)
                
                handler.seek(-2, 2)  # 从末尾向前2字节
                self.assertEqual(handler.tell(), len(self.test_content) - 2)

class TestTextFileHandler(unittest.TestCase):
    """文本文件处理器测试。"""
    
    def setUp(self):
        """测试准备。"""
        self.test_manager = TestFileManager()
        self.test_content = "Hello, 世界！".encode('utf-8')
        
    def tearDown(self):
        """测试清理。"""
        self.test_manager.cleanup()
        
    def test_read_text_file(self):
        """测试文本文件读取。"""
        with self.test_manager as manager:
            file_path = manager.create_file(self.test_content)
            
            handler = TextFileHandler(file_path, encoding='utf-8')
            with handler:
                content = handler.read()
                self.assertEqual(content, "Hello, 世界！")
                
    def test_invalid_encoding(self):
        """测试无效编码。"""
        with self.test_manager as manager:
            file_path = manager.create_file(self.test_content)
            
            with self.assertRaises(LookupError):
                TextFileHandler(file_path, encoding='invalid-encoding')
                
    def test_metadata(self):
        """测试元数据获取。"""
        with self.test_manager as manager:
            file_path = manager.create_file(self.test_content)
            
            handler = TextFileHandler(file_path, encoding='utf-8')
            metadata = handler.get_metadata()
            
            self.assertEqual(metadata['encoding'], 'utf-8')
            self.assertEqual(metadata['file_type'], 'text')
            self.assertEqual(metadata['file_size'], len(self.test_content))

class TestGzipFileHandler(unittest.TestCase):
    """GZIP文件处理器测试。"""
    
    def setUp(self):
        """测试准备。"""
        self.test_manager = TestFileManager()
        self.test_content = b"Hello, Compressed World!"
        
    def tearDown(self):
        """测试清理。"""
        self.test_manager.cleanup()
        
    def _create_gzip_file(self, content: bytes) -> Path:
        """创建GZIP测试文件。"""
        file_path = self.test_manager.create_file(b"", suffix='.gz')
        with gzip.open(file_path, 'wb') as f:
            f.write(content)
        return file_path
            
    def test_read_gzip_file(self):
        """测试GZIP文件读取。"""
        with self.test_manager as manager:
            file_path = self._create_gzip_file(self.test_content)
            
            handler = GzipFileHandler(file_path)
            with handler:
                content = handler.read()
                self.assertEqual(content, self.test_content.decode('utf-8'))
            
    def test_invalid_gzip_file(self):
        """测试无效的GZIP文件。"""
        with self.test_manager as manager:
            file_path = manager.create_file(b"Not a gzip file", suffix='.gz')
            
            with self.assertRaises(FileFormatError):
                GzipFileHandler(file_path)
                
    def test_metadata(self):
        """测试GZIP元数据。"""
        with self.test_manager as manager:
            file_path = self._create_gzip_file(self.test_content)
            
            handler = GzipFileHandler(file_path)
            metadata = handler.get_metadata()
            
            self.assertEqual(metadata['file_type'], 'gzip')
            self.assertIn('compressed_size', metadata)
            self.assertIn('mtime', metadata)

class TestFileHandlerFactory(unittest.TestCase):
    """文件处理器工厂测试。"""
    
    def setUp(self):
        """测试准备。"""
        self.factory = FileHandlerFactory()
        self.test_manager = TestFileManager()
        
    def tearDown(self):
        """测试清理。"""
        self.test_manager.cleanup()
        
    def test_create_text_handler(self):
        """测试创建文本文件处理器。"""
        with self.test_manager as manager:
            file_path = manager.create_file(b"text content", suffix='.txt')
            handler = self.factory.get_handler(file_path)
            
            self.assertIsInstance(handler, TextFileHandler)
            
    def test_create_gzip_handler(self):
        """测试创建GZIP文件处理器。"""
        with self.test_manager as manager:
            # 创建GZIP文件
            file_path = manager.create_file(b"", suffix='.gz')
            with gzip.open(file_path, 'wb') as f:
                f.write(b"gzip content")
                
            handler = self.factory.get_handler(file_path)
            
            self.assertIsInstance(handler, GzipFileHandler)
            
    def test_unsupported_extension(self):
        """测试不支持的文件扩展名。"""
        with self.test_manager as manager:
            file_path = manager.create_file(b"content", suffix='.unsupported')
            
            with self.assertRaises(FileFormatError):
                self.factory.get_handler(file_path)
                
    def test_custom_handler_registration(self):
        """测试自定义处理器注册。"""
        class CustomHandler(BaseFileHandler):
            def read(self, size: int = -1) -> bytes:
                return b""
                
        self.factory.register_handler(
            "custom",
            CustomHandler,
            [".cst"]
        )
        
        with self.test_manager as manager:
            file_path = manager.create_file(b"content", suffix='.cst')
            handler = self.factory.get_handler(file_path)
            
            self.assertIsInstance(handler, CustomHandler)
            
    def test_supported_types(self):
        """测试支持的文件类型。"""
        extensions = self.factory.supported_extensions
        handlers = self.factory.supported_handlers
        
        self.assertTrue(".txt" in extensions)
        self.assertTrue(".gz" in extensions)
        self.assertTrue("text" in handlers)
        self.assertTrue("gzip" in handlers)

if __name__ == '__main__':
    unittest.main()