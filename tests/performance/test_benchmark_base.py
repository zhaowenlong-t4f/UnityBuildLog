"""性能基准测试基础组件。"""

import pytest
import time
import psutil
import json
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

from tests.performance.test_utils import timeout


@dataclass
class BenchmarkMetrics:
    """基准测试指标数据。"""
    duration: float  # 执行时长（秒）
    memory_peak: float  # 内存峰值（MB）
    memory_avg: float  # 平均内存使用（MB）
    cpu_percent: float  # CPU使用率（百分比）
    io_read_mb: float  # IO读取量（MB）
    io_write_mb: float  # IO写入量（MB）
    additional_metrics: Dict[str, Any]  # 额外的指标数据


@dataclass
class BenchmarkResult:
    """基准测试结果。"""
    name: str  # 测试名称
    timestamp: str  # 执行时间戳
    metrics: BenchmarkMetrics  # 测试指标
    parameters: Dict[str, Any]  # 测试参数
    description: str  # 测试描述


class BenchmarkBase(ABC):
    """基准测试基类。"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        output_dir: Optional[Path] = None
    ):
        """初始化基准测试。

        Args:
            name: 测试名称
            description: 测试描述
            parameters: 测试参数
            output_dir: 结果输出目录
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.output_dir = output_dir or Path("benchmark_results")
        self._process = psutil.Process()
        self._start_time = 0.0
        self._memory_samples: List[float] = []
        self._io_start = None

    def setup(self) -> None:
        """设置测试环境。"""
        # 初始化基本指标
        self.metrics = BenchmarkMetrics(
            duration=0.0,
            memory_peak=0.0,
            memory_avg=0.0,
            cpu_percent=0.0,
            io_read_mb=0.0,
            io_write_mb=0.0,
            additional_metrics={}
        )

    @abstractmethod
    def execute(self) -> None:
        """执行测试。"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理测试资源。"""
        pass

    def _sample_metrics(self) -> None:
        """采集性能指标。"""
        memory = self._process.memory_info().rss / (1024 * 1024)  # 转换为MB
        self._memory_samples.append(memory)

    def _get_io_counters(self) -> tuple[float, float]:
        """获取IO计数器。

        Returns:
            读取和写入的字节数（MB）的元组
        """
        io = self._process.io_counters()
        return (
            io.read_bytes / (1024 * 1024),
            io.write_bytes / (1024 * 1024)
        )

    @timeout(180)  # 每个测试用例3分钟超时
    def run(self) -> BenchmarkResult:
        """运行基准测试。

        Returns:
            基准测试结果

        Raises:
            TimeoutError: 如果测试执行超时
        """
        # 初始化计数器
        self._memory_samples.clear()
        self._io_start = self._get_io_counters()
        self._start_time = time.time()

        try:
            # 设置和执行测试
            self.setup()
            self.execute()
        except TimeoutError:
            self.cleanup()  # 确保在超时时也进行清理
            raise
        except Exception as e:
            self.cleanup()  # 确保在出错时也进行清理
            raise

        # 采集最终指标
        end_time = time.time()
        duration = end_time - self._start_time
        io_end = self._get_io_counters()

        # 计算指标
        metrics = BenchmarkMetrics(
            duration=duration,
            memory_peak=max(self._memory_samples),
            memory_avg=sum(self._memory_samples) / len(self._memory_samples),
            cpu_percent=self._process.cpu_percent(),
            io_read_mb=io_end[0] - self._io_start[0],
            io_write_mb=io_end[1] - self._io_start[1],
            additional_metrics={}
        )

        # 清理资源
        self.cleanup()

        # 创建结果
        result = BenchmarkResult(
            name=self.name,
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            parameters=self.parameters,
            description=self.description
        )

        # 保存结果
        self._save_result(result)

        return result

    def _save_result(self, result: BenchmarkResult) -> None:
        """保存测试结果。

        Args:
            result: 要保存的测试结果
        """
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 构建结果文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result.name}_{timestamp}.json"
        filepath = self.output_dir / filename

        # 转换结果为字典
        result_dict = {
            "name": result.name,
            "timestamp": result.timestamp,
            "description": result.description,
            "parameters": result.parameters,
            "metrics": {
                "duration": result.metrics.duration,
                "memory_peak": result.metrics.memory_peak,
                "memory_avg": result.metrics.memory_avg,
                "cpu_percent": result.metrics.cpu_percent,
                "io_read_mb": result.metrics.io_read_mb,
                "io_write_mb": result.metrics.io_write_mb,
                "additional_metrics": result.metrics.additional_metrics
            }
        }

        # 保存为JSON文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)


def pytest_generate_tests(metafunc):
    """pytest参数化函数，用于生成测试用例。"""
    if "benchmark_params" in metafunc.fixturenames:
        # 从配置文件加载测试参数
        config_path = Path("tests/performance/benchmark_config.json")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                configs = json.load(f)
            metafunc.parametrize("benchmark_params", configs)
        else:
            metafunc.parametrize("benchmark_params", [{}])  # 默认参数