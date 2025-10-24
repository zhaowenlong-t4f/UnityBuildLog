"""缓存效率性能基准测试。"""

import pytest
import random
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from tests.performance.test_benchmark_base import BenchmarkBase
from src.log_parser.reader.cache import CacheManager
from src.log_parser.reader.monitoring import StatsCollector
from tests.performance.test_cache_strategy import LRUTestStrategy


class CacheEfficiencyBenchmark(BenchmarkBase):
    """缓存效率性能测试基准。"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        output_dir: Optional[Path] = None
    ):
        """初始化缓存效率基准测试。

        Args:
            name: 测试名称
            description: 测试描述
            parameters: 测试参数，必须包含：
                - cache_size: 缓存大小限制（MB）
                - item_count: 缓存项目数量
                - item_size: 每个缓存项的大小（KB）
                - access_pattern: 访问模式 ('random', 'sequential', 'zipf')
                - operation_count: 操作次数
            output_dir: 结果输出目录
        """
        super().__init__(name, description, parameters, output_dir)
        self.cache_manager: Optional[CacheManager] = None
        self.stats_collector: Optional[StatsCollector] = None
        self.items: Dict[str, bytes] = {}

    def _generate_test_data(self) -> Dict[str, bytes]:
        """生成测试数据。

        Returns:
            键值对形式的测试数据
        """
        item_count = self.parameters["item_count"]
        item_size_kb = self.parameters["item_size"]
        
        items = {}
        for i in range(item_count):
            # 生成指定大小的随机数据
            data = os.urandom(item_size_kb * 1024)
            items[f"item_{i}"] = data
            
        return items

    def _get_access_sequence(self) -> List[str]:
        """根据指定的访问模式生成访问序列。

        Returns:
            要访问的键的列表
        """
        pattern = self.parameters["access_pattern"]
        operation_count = self.parameters["operation_count"]
        keys = list(self.items.keys())
        
        if pattern == "sequential":
            # 顺序访问
            return [keys[i % len(keys)] for i in range(operation_count)]
            
        elif pattern == "random":
            # 随机访问
            return [random.choice(keys) for _ in range(operation_count)]
            
        elif pattern == "zipf":
            # Zipf分布 - 模拟现实世界的缓存访问模式
            # 80%的访问集中在20%的数据上
            hot_set_size = int(len(keys) * 0.2)
            hot_set = set(random.sample(keys, hot_set_size))
            
            sequence = []
            for _ in range(operation_count):
                if random.random() < 0.8:  # 80%概率访问热点数据
                    sequence.append(random.choice(list(hot_set)))
                else:  # 20%概率访问其他数据
                    cold_set = set(keys) - hot_set
                    sequence.append(random.choice(list(cold_set)))
            
            return sequence
        
        raise ValueError(f"Unsupported access pattern: {pattern}")

    def setup(self) -> None:
        """设置测试环境。"""
        # 调用父类的setup以初始化metrics
        super().setup()
        
        # 生成测试数据
        self.items = self._generate_test_data()
        
        # 初始化缓存管理器
        max_size = self.parameters["cache_size"] * 1024 * 1024  # 转换为字节
        strategy = LRUTestStrategy()  # 使用测试用的LRU策略
        self.cache_manager = CacheManager(
            strategy=strategy,
            max_size=max_size
        )
        
        # 初始化统计收集器
        self.stats_collector = StatsCollector()  # StatsCollector 不需要显式启动
        
        # 初始化额外的指标
        self.metrics.additional_metrics.update({
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0
        })

    def execute(self) -> None:
        """执行测试。"""
        # 获取访问序列
        access_sequence = self._get_access_sequence()
        
        # 执行缓存操作
        for key in access_sequence:
            if not self.cache_manager.has(key):
                # 缓存未命中，添加到缓存
                self.cache_manager.put(key, self.items[key])
                self.stats_collector.record_cache_miss()
            else:
                # 缓存命中，获取数据
                _ = self.cache_manager.get(key)
                self.stats_collector.record_cache_hit()
            
            self._sample_metrics()

        # 记录额外的指标
        stats = self.stats_collector.get_statistics()
        cache_stats = stats["cache"]
        self.metrics.additional_metrics.update({
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            "hit_rate": cache_stats["hit_ratio"]
        })

    def cleanup(self) -> None:
        """清理测试资源。"""
        if self.cache_manager:
            self.cache_manager.clear()
        
        self.items.clear()


@pytest.mark.parametrize("cache_size", [64, 128, 256])  # MB
@pytest.mark.parametrize("item_count", [100, 500, 1000])
@pytest.mark.parametrize("item_size", [64, 256, 1024])  # KB
@pytest.mark.parametrize("access_pattern", ["random", "sequential", "zipf"])
@pytest.mark.parametrize("operation_count", [1000, 5000])
def test_cache_efficiency(
    cache_size: int,
    item_count: int,
    item_size: int,
    access_pattern: str,
    operation_count: int,
    benchmark_params: Dict[str, Any]
):
    """测试缓存效率。"""
    # 合并配置参数
    parameters = {
        "cache_size": cache_size,
        "item_count": item_count,
        "item_size": item_size,
        "access_pattern": access_pattern,
        "operation_count": operation_count,
        **benchmark_params
    }
    
    # 创建并运行基准测试
    benchmark = CacheEfficiencyBenchmark(
        name=f"cache_efficiency_{access_pattern}_{cache_size}mb",
        description=f"Testing cache efficiency with {access_pattern} access pattern",
        parameters=parameters
    )
    
    result = benchmark.run()
    
    # 验证结果
    assert result.metrics.duration > 0
    assert result.metrics.memory_peak > 0
    assert result.metrics.memory_peak <= cache_size * 2  # 确保内存使用在合理范围内
    
    # 验证缓存效率指标
    hit_rate = result.metrics.additional_metrics["hit_rate"]
    if access_pattern == "sequential":
        # 顺序访问应该有较高的命中率
        assert hit_rate >= 0.7  # 期望至少70%的命中率
    elif access_pattern == "zipf":
        # Zipf分布应该有中等的命中率
        assert hit_rate >= 0.5  # 期望至少50%的命中率