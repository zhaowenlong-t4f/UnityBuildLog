"""文件读取性能基准测试。"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional

from tests.performance.test_benchmark_base import BenchmarkBase
from src.log_parser.reader.iterators import ChunkIterator, LineIterator
from src.log_parser.reader.file_handlers import TextFileHandler


class FileReadingBenchmark(BenchmarkBase):
    """文件读取性能测试基准。"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        output_dir: Optional[Path] = None
    ):
        """初始化文件读取基准测试。

        Args:
            name: 测试名称
            description: 测试描述
            parameters: 测试参数，必须包含：
                - file_size: 测试文件大小（MB）
                - buffer_size: 读取缓冲区大小（bytes）
                - iterator_type: 迭代器类型（'chunk' 或 'line'）
                - chunk_size: 分块大小（仅用于ChunkIterator）
            output_dir: 结果输出目录
        """
        super().__init__(name, description, parameters, output_dir)
        self.test_file: Optional[Path] = None
        self.file_handler: Optional[TextFileHandler] = None
        self.iterator = None

    def _create_test_file(self) -> Path:
        """创建测试用大文件。

        Returns:
            测试文件路径
        """
        # 创建临时文件
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        
        # 计算需要写入的行数
        file_size_mb = self.parameters["file_size"]
        bytes_per_line = 100  # 假设每行平均100字节
        total_lines = int((file_size_mb * 1024 * 1024) / bytes_per_line)
        
        # 生成测试数据
        with open(path, "w", encoding="utf-8") as f:
            for i in range(total_lines):
                # 生成模拟的Unity构建日志行
                log_line = f"[{i:08d}] Building scene {i%100:03d}: Some detailed log message with various parameters and values.\n"
                f.write(log_line)
        
        return Path(path)

    def setup(self) -> None:
        """设置测试环境。"""
        # 创建测试文件
        self.test_file = self._create_test_file()
        
        # 初始化文件处理器并打开文件
        self.file_handler = TextFileHandler(
            self.test_file,
            buffer_size=self.parameters["buffer_size"]
        )
        self.file_handler.open()
        
        # 根据参数创建迭代器
        if self.parameters["iterator_type"] == "chunk":
            self.iterator = ChunkIterator(
                self.file_handler,
                chunk_size=self.parameters["chunk_size"]
            )
        else:  # line
            self.iterator = LineIterator(self.file_handler)

    def execute(self) -> None:
        """执行测试。"""
        # 读取整个文件
        for _ in self.iterator:
            self._sample_metrics()  # 定期采样性能指标

    def cleanup(self) -> None:
        """清理测试资源。"""
        if self.file_handler:
            self.file_handler.close()
        
        if self.test_file and self.test_file.exists():
            self.test_file.unlink()


@pytest.mark.parametrize("file_size", [10, 100, 500])  # MB
@pytest.mark.parametrize("buffer_size", [4096, 8192, 16384])  # bytes
@pytest.mark.parametrize("iterator_type", ["chunk", "line"])
@pytest.mark.parametrize("chunk_size", [1024, 4096])  # bytes，仅用于ChunkIterator
def test_file_reading_performance(
    file_size: int,
    buffer_size: int,
    iterator_type: str,
    chunk_size: int,
    benchmark_params: Dict[str, Any]
):
    """测试文件读取性能。"""
    # 合并配置参数
    parameters = {
        "file_size": file_size,
        "buffer_size": buffer_size,
        "iterator_type": iterator_type,
        "chunk_size": chunk_size,
        **benchmark_params
    }
    
    # 创建并运行基准测试
    benchmark = FileReadingBenchmark(
        name=f"file_reading_{iterator_type}_{file_size}mb",
        description=f"Testing {iterator_type} iterator performance with {file_size}MB file",
        parameters=parameters
    )
    
    result = benchmark.run()
    
    # 验证结果
    assert result.metrics.duration > 0
    assert result.metrics.memory_peak > 0
    assert result.metrics.io_read_mb > 0