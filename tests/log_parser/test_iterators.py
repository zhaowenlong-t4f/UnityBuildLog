"""
测试日志文件迭代器相关功能
"""
import unittest
from unittest.mock import Mock, patch
from io import StringIO

from src.log_parser.reader.iterators.chunk_iterator import ChunkIterator
from src.log_parser.reader.iterators.line_iterator import LineIterator
from src.log_parser.reader.exceptions import ReadError

class TestChunkIterator(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.test_content = "第一行\n第二行\n第三行很长很长很长很长很长很长\n第四行\n"
        self.mock_file = StringIO(self.test_content)
        self.file_handler = Mock(spec=StringIO)
        self.file_handler.read.side_effect = self.mock_file.read
        self.file_handler.seek.side_effect = self.mock_file.seek
        self.file_handler.tell.side_effect = self.mock_file.tell

    def test_chunk_iteration(self):
        """测试基本的分片迭代功能"""
        iterator = ChunkIterator(self.file_handler, chunk_size=10)
        chunks = list(iterator)
        
        # 验证所有分片合并后等于原始内容
        self.assertEqual(''.join(chunks), self.test_content)

    def test_chunk_boundary_handling(self):
        """测试分片边界处理"""
        # 使用较小的分片大小来测试边界处理
        iterator = ChunkIterator(self.file_handler, chunk_size=5)
        chunks = list(iterator)
        
        # 验证分片合并后内容完整
        self.assertEqual(''.join(chunks), self.test_content)
        
        # 验证每个分片都以换行符结束（最后一个分片除外）
        for chunk in chunks[:-1]:
            self.assertTrue(chunk.endswith('\n'))

    def test_reset_functionality(self):
        """测试重置功能"""
        iterator = ChunkIterator(self.file_handler)
        first_chunk = next(iterator)
        iterator.reset()
        
        # 重置后再次读取，应该获得相同的内容
        new_first_chunk = next(iterator)
        self.assertEqual(first_chunk, new_first_chunk)

    def test_seek_and_tell(self):
        """测试seek和tell功能"""
        iterator = ChunkIterator(self.file_handler)
        
        # 记录初始位置
        initial_pos = iterator.tell()
        self.assertEqual(initial_pos, 0)
        
        # 读取一些内容后检查位置
        next(iterator)
        self.assertGreater(iterator.tell(), initial_pos)
        
        # 测试seek
        iterator.seek(0)
        self.assertEqual(iterator.tell(), 0)

    def test_error_handling(self):
        """测试错误处理"""
        # 设置新的mock以模拟错误
        error_handler = Mock(spec=StringIO)
        error_handler.read.side_effect = Exception("模拟的读取错误")
        iterator = ChunkIterator(error_handler)
        
        with self.assertRaises(ReadError):
            next(iterator)
    
    def test_binary_mode(self):
        """测试二进制模式的类型处理"""
        from io import BytesIO
        content = "第一行\n第二行\n".encode('utf-8')
        mock_file = BytesIO(content)
        file_handler = Mock(wraps=mock_file)  # 使用wraps而不是spec来保留mode属性
        file_handler.mode = 'rb'
        
        iterator = ChunkIterator(file_handler, chunk_size=5)
        chunks = list(iterator)
        
        # 验证每个分片都是bytes类型
        self.assertTrue(all(isinstance(chunk, bytes) for chunk in chunks), 
                      "不是所有的分片都是bytes类型")
        # 验证分片合并后等于原始内容
        self.assertEqual(b''.join(chunks), content, 
                      "合并后的内容与原始内容不匹配")


class TestLineIterator(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.test_content = "第一行\n第二行\n第三行很长很长很长很长很长很长\n第四行\n"
        self.mock_file = StringIO(self.test_content)
        self.file_handler = Mock(spec=StringIO)
        self.file_handler.read.side_effect = self.mock_file.read
        self.file_handler.seek.side_effect = self.mock_file.seek
        self.file_handler.tell.side_effect = self.mock_file.tell

    def test_line_iteration(self):
        """测试基本的行迭代功能"""
        iterator = LineIterator(self.file_handler)
        lines = list(iterator)
        
        # 验证行数
        self.assertEqual(len(lines), 4)
        # 验证每行都以换行符结束
        for line in lines:
            self.assertTrue(line.endswith('\n'))

    def test_line_number_tracking(self):
        """测试行号跟踪"""
        iterator = LineIterator(self.file_handler)
        
        # 读取两行
        next(iterator)
        next(iterator)
        self.assertEqual(iterator.get_line_number(), 2)
        
        # 读取剩余行
        list(iterator)
        self.assertEqual(iterator.get_line_number(), 4)

    def test_max_line_length(self):
        """测试最大行长度限制"""
        # 创建一个非常长的行
        long_line = "x" * 2000 + "\n"
        mock_file = StringIO(long_line)
        file_handler = Mock(spec=StringIO)
        file_handler.read.side_effect = mock_file.read
        file_handler.seek.side_effect = mock_file.seek
        file_handler.tell.side_effect = mock_file.tell
        
        iterator = LineIterator(file_handler, max_line_length=1000)
        lines = list(iterator)
        
        # 验证长行被正确分割
        self.assertGreater(len(lines), 1)  # 确保行被分割
        self.assertTrue(all(len(line) <= 1001 for line in lines))  # 1001包含换行符
        self.assertEqual(''.join(lines), long_line)  # 确保内容完整性

    def test_buffer_handling(self):
        """测试缓冲区处理"""
        iterator = LineIterator(self.file_handler, buffer_size=10)
        lines = list(iterator)
        
        # 验证所有行合并后等于原始内容
        self.assertEqual(''.join(lines), self.test_content)

    def test_reset_functionality(self):
        """测试重置功能"""
        iterator = LineIterator(self.file_handler)
        first_line = next(iterator)
        iterator.reset()
        
        # 重置后再次读取，应该获得相同的行
        new_first_line = next(iterator)
        self.assertEqual(first_line, new_first_line)
        self.assertEqual(iterator.get_line_number(), 1)

    def test_error_handling(self):
        """测试错误处理"""
        # 设置新的mock以模拟错误
        error_handler = Mock(spec=StringIO)
        error_handler.read.side_effect = Exception("模拟的读取错误")
        iterator = LineIterator(error_handler)
        
        with self.assertRaises(ReadError):
            next(iterator)


if __name__ == '__main__':
    unittest.main()