"""内存使用性能基准测试。"""

import pytest
import gc
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from tests.performance.test_benchmark_base import BenchmarkBase
from src.log_parser.reader.monitoring import MemoryMonitor
from src.log_parser.reader.cache import CacheManager
from tests.performance.test_cache_strategy import LRUTestStrategy
from src.log_parser.reader.file_handlers import TextFileHandler
from src.log_parser.reader.iterators import ChunkIterator


class MemoryUsageBenchmark(BenchmarkBase):
    """内存使用性能测试基准。"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        output_dir: Optional[Path] = None
    ):
        """初始化内存使用基准测试。

        Args:
            name: 测试名称
            description: 测试描述
            parameters: 测试参数，必须包含：
                - file_size: 测试文件大小（MB）
                - cache_size: 缓存大小限制（MB）
                - operation_count: 重复操作次数
            output_dir: 结果输出目录
        """
        super().__init__(name, description, parameters, output_dir)
        self.test_files: List[Path] = []
        self.cache_manager: Optional[CacheManager] = None
        self.memory_monitor: Optional[MemoryMonitor] = None

    def _create_test_files(self, count: int = 5) -> List[Path]:
        """创建多个测试文件。

        Args:
            count: 要创建的文件数量

        Returns:
            测试文件路径列表
        """
        paths = []
        file_size_mb = self.parameters["file_size"] / count  # 平均分配总大小
        
        for i in range(count):
            fd, path = tempfile.mkstemp(suffix=f"_{i}.txt")
            os.close(fd)
            
            try:
                # 计算每个文件的行数
                bytes_per_line = 100
                total_lines = int((file_size_mb * 1024 * 1024) / bytes_per_line)
                
                # 生成测试数据
                with open(path, "w", encoding="utf-8") as f:
                    for j in range(total_lines):
                        log_line = f"[File_{i}][{j:08d}] Memory test log line with varying content and size.\n"
                        f.write(log_line)
                
                print(f"已创建测试文件：{path} ({file_size_mb:.1f}MB)")
            except (IOError, OSError) as e:
                print(f"创建测试文件 {path} 失败：{str(e)}")
                continue
            
            paths.append(Path(path))
        
        return paths

    def setup(self) -> None:
        """设置测试环境。"""
        # 调用父类setup以初始化metrics
        super().setup()
        
        # 清理之前的缓存和强制GC
        gc.collect()
        
        # 创建测试文件
        self.test_files = self._create_test_files()
        
        # 初始化缓存管理器
        max_size = self.parameters["cache_size"] * 1024 * 1024  # 转换为字节
        self.cache_manager = CacheManager(
            strategy=LRUTestStrategy(),  # 使用LRU缓存策略
            max_size=max_size
        )        # 初始化内存监控
        self.memory_monitor = MemoryMonitor(
            threshold=0.8,  # 设置内存使用率阈值为80%
            sampling_interval=1.0  # 每秒采样一次
        )
        self.memory_monitor.start_monitoring()

    def execute(self) -> None:
        """执行测试。"""
        operation_count = self.parameters["operation_count"]
        
        for _ in range(operation_count):
            for file_path in self.test_files:
                # 从缓存获取或读取文件
                if not self.cache_manager.has(str(file_path)):
                    try:
                        with open(file_path, "rb") as f:  # 直接使用二进制模式打开
                            iterator = ChunkIterator(f)
                            content = b"".join(chunk for chunk in iterator)
                            self.cache_manager.put(str(file_path), content)
                    except (FileNotFoundError, IOError) as e:
                        print(f"文件 {file_path} 操作失败：{str(e)}")
                        continue
                else:
                    _ = self.cache_manager.get(str(file_path))
                
                self._sample_metrics()
                
                # 模拟一些内存压力
                temp_data = [b"x" * 1024 * 1024]  # 分配1MB
                _ = self.memory_monitor.check_memory()
                del temp_data  # 释放内存

    def cleanup(self) -> None:
        """清理测试资源。"""
        # 停止内存监控
        if self.memory_monitor:
            self.memory_monitor.stop_monitoring()
        
        # 清理缓存
        if self.cache_manager:
            self.cache_manager.clear()
        
        # 删除测试文件
        for file_path in self.test_files:
            if file_path.exists():
                file_path.unlink()
        
        # 强制GC
        gc.collect()


@pytest.mark.parametrize("file_size", [50, 200, 500])  # MB
@pytest.mark.parametrize("cache_size", [64, 128, 256])  # MB
@pytest.mark.parametrize("operation_count", [5, 10])
def test_memory_usage(
    file_size: int,
    cache_size: int,
    operation_count: int,
    benchmark_params: Dict[str, Any]
):
    """测试内存使用性能。"""
    # 合并配置参数
    parameters = {
        "file_size": file_size,
        "cache_size": cache_size,
        "operation_count": operation_count,
        **benchmark_params
    }
    
    # 创建并运行基准测试
    benchmark = MemoryUsageBenchmark(
        name=f"memory_usage_{file_size}mb_{cache_size}mb_cache",
        description=f"Testing memory usage with {file_size}MB total file size and {cache_size}MB cache",
        parameters=parameters
    )
    
    result = benchmark.run()
    
    # 验证结果
    assert result.metrics.duration > 0
    assert result.metrics.memory_peak > 0
    assert result.metrics.memory_peak <= cache_size * 3  # 确保峰值不超过预期
    assert result.metrics.memory_avg <= cache_size * 2  # 确保平均值在合理范围内