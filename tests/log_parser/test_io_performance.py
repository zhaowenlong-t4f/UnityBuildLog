import os
import time
import pytest
from src.log_parser.reader.file_handlers import TextFileHandler, GzipFileHandler
from src.log_parser.reader.iterators import ChunkIterator, LineIterator

# 设置默认超时时间为30秒
pytestmark = pytest.mark.timeout(30)

class TestIOPerformance:
    @pytest.fixture(params=[
        (1, "1MB"),       # 1MB
        (10, "10MB"),     # 10MB
        (100, "100MB"),   # 100MB
        (500, "500MB"),   # 500MB
    ])
    def test_file(self, tmp_path, request):
        """创建不同大小的测试文件

        Args:
            tmp_path: pytest提供的临时目录
            request: pytest的request对象，包含参数信息

        Returns:
            tuple: (文件路径, 文件大小描述)
        """
        size_mb, size_desc = request.param
        file_path = tmp_path / f"test_{size_desc}.txt"
        
        # 计算需要写入的行数（每行约120字节）
        lines_count = (size_mb * 1024 * 1024) // 120

        with open(file_path, "w") as f:
            for i in range(lines_count):
                f.write(f"Test line {i}: {'*' * 100}\n")
                
        return str(file_path), size_desc

    def measure_performance(self, func, *args):
        """测量函数执行时间和内存使用"""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        result = func(*args)
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        return {
            'execution_time': end_time - start_time,
            'memory_used': end_memory - start_memory,
            'result': result
        }

    def get_memory_usage(self):
        """获取当前进程的内存使用"""
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss

    def test_chunk_iterator_auto_performance(self, test_file):
        """测试ChunkIterator的自适应buffer_size性能"""
        file_path, size_desc = test_file
        handler = TextFileHandler(file_path)
        try:
            handler.open()
            iterator = ChunkIterator(handler)  # 使用自适应buffer_size
            
            def read_all_chunks():
                chunks = []
                for chunk in iterator:
                    chunks.append(len(chunk))
                return sum(chunks)

            perf_data = self.measure_performance(read_all_chunks)
            
            buffer_size = iterator.chunk_size
            print(f"\nChunkIterator Performance ({size_desc}, auto buffer_size={buffer_size}):")
            print(f"Execution time: {perf_data['execution_time']:.2f} seconds")
            print(f"Memory used: {perf_data['memory_used'] / 1024 / 1024:.2f} MB")
            print(f"Total bytes read: {perf_data['result']}")

            # 记录性能数据
            return {
                'file_size': size_desc,
                'auto_buffer_size': buffer_size,
                'execution_time': perf_data['execution_time'],
                'memory_used': perf_data['memory_used'],
                'bytes_read': perf_data['result']
            }
        finally:
            handler.close()

    @pytest.mark.parametrize("buffer_size", [
        4096,      # 4KB
        8192,      # 8KB
        16384,     # 16KB
        32768,     # 32KB
        65536,     # 64KB
    ])
    def test_line_iterator_performance(self, test_file, buffer_size):
        """测试不同buffer_size下LineIterator的性能"""
        file_path, size_desc = test_file
        handler = TextFileHandler(file_path)
        try:
            handler.open()
            iterator = LineIterator(handler, buffer_size=buffer_size)
            
            def read_all_lines():
                lines = []
                for line in iterator:
                    lines.append(len(line))
                return sum(lines)

            perf_data = self.measure_performance(read_all_lines)
            
            print(f"\nLineIterator Performance ({size_desc}, buffer_size={buffer_size}):")
            print(f"Execution time: {perf_data['execution_time']:.2f} seconds")
            print(f"Memory used: {perf_data['memory_used'] / 1024 / 1024:.2f} MB")
            print(f"Total bytes read: {perf_data['result']}")

            return {
                'file_size': size_desc,
                'buffer_size': buffer_size,
                'execution_time': perf_data['execution_time'],
                'memory_used': perf_data['memory_used'],
                'bytes_read': perf_data['result']
            }
        finally:
            handler.close()

    @pytest.mark.parametrize("file_size_mb", [1, 10, 100])
    def test_gzip_performance(self, tmp_path, file_size_mb):
        """测试GZIP文件处理性能"""
        import gzip
        
        # 计算需要写入的行数（每行约120字节）
        lines_count = (file_size_mb * 1024 * 1024) // 120
        
        # 创建测试用的GZIP文件
        gz_file = tmp_path / f"test_{file_size_mb}MB.txt.gz"
        with gzip.open(gz_file, 'wb') as f:
            for i in range(lines_count):
                f.write(f"Test line {i}: {'*' * 100}\n".encode())

        handler = GzipFileHandler(str(gz_file))
        try:
            handler.open()
            iterator = ChunkIterator(handler)
            
            def read_gzip_file():
                chunks = []
                for chunk in iterator:
                    chunks.append(len(chunk))
                return sum(chunks)

            perf_data = self.measure_performance(read_gzip_file)
            
            print(f"\nGZIP File Reading Performance ({file_size_mb}MB):")
            print(f"Execution time: {perf_data['execution_time']:.2f} seconds")
            print(f"Memory used: {perf_data['memory_used'] / 1024 / 1024:.2f} MB")
            print(f"Total bytes read: {perf_data['result']}")

            return {
                'file_size': f"{file_size_mb}MB",
                'execution_time': perf_data['execution_time'],
                'memory_used': perf_data['memory_used'],
                'bytes_read': perf_data['result']
            }
        finally:
            handler.close()