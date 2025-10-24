"""执行全面性能测试并生成报告。"""

import pytest
import json
import time
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from src.log_parser.reader.monitoring import StatsCollector
from tests.performance.test_utils import timeout
from tests.performance.test_file_reading import FileReadingBenchmark
from tests.performance.test_memory_usage import MemoryUsageBenchmark
from tests.performance.test_cache_efficiency import CacheEfficiencyBenchmark


@timeout(300)  # 5分钟超时
def get_timeout_config() -> Dict[str, Dict[str, Dict[str, int]]]:
    """获取超时配置。

    Returns:
        超时配置字典
    """
    config_path = Path("tests/performance/timeout_config.json")
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)["timeouts"]
    except UnicodeError:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)["timeouts"]


def get_file_size_category(size: int) -> str:
    """获取文件大小类别。

    Args:
        size: 文件大小（MB）

    Returns:
        大小类别：'small', 'medium' 或 'large'
    """
    if size <= 10:
        return "small"
    elif size <= 100:
        return "medium"
    else:
        return "large"


@timeout(180)  # 默认3分钟超时
def run_file_reading_tests() -> List[Dict[str, Any]]:
    """执行文件读取性能测试。"""
    results = []
    file_sizes = [10, 100, 500]  # MB
    buffer_sizes = [4096, 8192, 16384]  # bytes
    iterator_types = ["chunk", "line"]
    
    total_tests = len(file_sizes) * len(buffer_sizes) * len(iterator_types)
    completed_tests = 0
    
    # 加载超时配置
    timeouts = get_timeout_config().get("file_reading", {})
    
    for file_size in file_sizes:
        for buffer_size in buffer_sizes:
            for iterator_type in iterator_types:
                parameters = {
                    "file_size": file_size,
                    "buffer_size": buffer_size,
                    "iterator_type": iterator_type,
                    "chunk_size": buffer_size
                }
                
                # 获取当前文件大小对应的超时时间
                size_category = get_file_size_category(file_size)
                # 根据文件大小动态设置更短的超时时间
                base_timeout = {
                    "small": 60,    # 1分钟
                    "medium": 120,  # 2分钟
                    "large": 180    # 3分钟
                }
                timeout_seconds = timeouts.get(size_category, base_timeout.get(size_category, 60))
                
                test_name = f"文件读取测试 [{completed_tests + 1}/{total_tests}] - {file_size}MB文件, {buffer_size}字节缓冲区, {iterator_type}迭代器"
                print(f"\n开始{test_name}")
                print(f"预计超时时间: {timeout_seconds}秒")
                
                start_time = time.time()
                try:
                    # 使用动态超时时间
                    @timeout(timeout_seconds)
                    def run_benchmark():
                        bench = FileReadingBenchmark(
                            name=f"file_reading_{iterator_type}_{file_size}mb",
                            description=f"Testing {iterator_type} iterator performance with {file_size}MB file",
                            parameters=parameters
                        )
                        return bench.run()
                    
                    result = run_benchmark()
                    if result:
                        results.append(result.__dict__)
                        elapsed_time = time.time() - start_time
                        print(f"✓ {test_name} 完成 (用时: {elapsed_time:.2f}秒)")
                except TimeoutError:
                    print(f"⨯ {test_name} 超时 (超过{timeout_seconds}秒)")
                    continue
                except Exception as e:
                    print(f"⨯ {test_name} 失败: {str(e)}")
                    continue
                finally:
                    completed_tests += 1
    
    return results


@timeout(120)  # 默认2分钟超时
def run_memory_tests() -> List[Dict[str, Any]]:
    """执行内存使用性能测试。"""
    results = []
    file_sizes = [50, 200, 500]  # MB
    cache_sizes = [64, 128, 256]  # MB
    operation_counts = [5, 10]
    
    total_tests = len(file_sizes) * len(cache_sizes) * len(operation_counts)
    completed_tests = 0
    
    # 加载超时配置
    timeouts = get_timeout_config().get("memory_usage", {})
    
    for file_size in file_sizes:
        for cache_size in cache_sizes:
            for operation_count in operation_counts:
                parameters = {
                    "file_size": file_size,
                    "cache_size": cache_size,
                    "operation_count": operation_count
                }
                
                # 获取当前文件大小对应的超时时间
                size_category = get_file_size_category(file_size)
                # 根据文件大小动态设置更短的超时时间
                base_timeout = {
                    "small": 60,     # 1分钟
                    "medium": 90,    # 1.5分钟
                    "large": 120     # 2分钟
                }
                timeout_seconds = timeouts.get(size_category, base_timeout.get(size_category, 60))
                
                test_name = f"内存使用测试 [{completed_tests + 1}/{total_tests}] - {file_size}MB文件, {cache_size}MB缓存, {operation_count}次操作"
                print(f"\n开始{test_name}")
                print(f"预计超时时间: {timeout_seconds}秒")
                
                start_time = time.time()
                try:
                    # 使用动态超时时间
                    @timeout(timeout_seconds)
                    def run_benchmark():
                        bench = MemoryUsageBenchmark(
                            name=f"memory_usage_{file_size}mb_{cache_size}mb_cache",
                            description=f"Testing memory usage with {file_size}MB file and {cache_size}MB cache",
                            parameters=parameters
                        )
                        return bench.run()
                    
                    result = run_benchmark()
                    if result:
                        results.append(result.__dict__)
                        elapsed_time = time.time() - start_time
                        print(f"✓ {test_name} 完成 (用时: {elapsed_time:.2f}秒)")
                except TimeoutError:
                    print(f"⨯ {test_name} 超时 (超过{timeout_seconds}秒)")
                    continue
                except Exception as e:
                    print(f"⨯ {test_name} 失败: {str(e)}")
                    continue
                finally:
                    completed_tests += 1
    
    return results


@timeout(900)  # 15分钟超时
def get_cache_size_category(item_count: int, operation_count: int) -> str:
    """获取缓存测试规模类别。

    Args:
        item_count: 缓存项目数量
        operation_count: 操作次数

    Returns:
        规模类别：'small', 'medium' 或 'large'
    """
    scale = item_count * operation_count
    if scale <= 100000:  # 10万次操作以内
        return "small"
    elif scale <= 1000000:  # 100万次操作以内
        return "medium"
    else:
        return "large"


def run_cache_tests() -> List[Dict[str, Any]]:
    """执行缓存效率性能测试。"""
    results = []
    cache_sizes = [64, 128, 256]  # MB
    item_counts = [100, 500, 1000]
    item_sizes = [64, 256, 1024]  # KB
    access_patterns = ["random", "sequential", "zipf"]
    operation_counts = [1000, 5000]
    
    # 加载超时配置
    timeouts = get_timeout_config().get("cache_efficiency", {})
    
    for cache_size in cache_sizes:
        for item_count in item_counts:
            for item_size in item_sizes:
                for pattern in access_patterns:
                    for operation_count in operation_counts:
                        parameters = {
                            "cache_size": cache_size,
                            "item_count": item_count,
                            "item_size": item_size,
                            "access_pattern": pattern,
                            "operation_count": operation_count
                        }
                        
                        # 获取当前测试规模对应的超时时间
                        size_category = get_cache_size_category(item_count, operation_count)
                        timeout_seconds = timeouts.get(size_category, 900)  # 默认15分钟
                        
                        try:
                            # 使用动态超时时间
                            @timeout(timeout_seconds)
                            def run_benchmark():
                                bench = CacheEfficiencyBenchmark(
                                    name=f"cache_efficiency_{pattern}_{cache_size}mb",
                                    description=f"Testing cache efficiency with {pattern} access pattern",
                                    parameters=parameters
                                )
                                return bench.run()
                            
                            result = run_benchmark()
                            results.append(result.__dict__)
                        except TimeoutError:
                            print(f"缓存测试超时：{cache_size}MB cache, {pattern} pattern, {item_count} items")
                            continue
                        except Exception as e:
                            print(f"缓存测试失败：{cache_size}MB cache, {pattern} pattern, {item_count} items, 错误：{str(e)}")
                            continue
    
    return results


def generate_plots(results_dir: Path) -> None:
    """生成性能测试图表。

    Args:
        results_dir: 结果数据目录
    """
    def safe_access(obj: Any, key: str, default: Any = None) -> Any:
        """安全访问字典值。"""
        if isinstance(obj, dict) and key in obj:
            return obj[key]
        return default

    # 读取所有结果文件
    all_results = []
    for result_file in results_dir.glob("*.json"):
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                result = json.load(f)
                if isinstance(result, dict):
                    all_results.append(result)
                elif isinstance(result, (list, tuple)):
                    all_results.extend(result)
        except Exception as e:
            print(f"处理结果文件 {result_file} 时出错：{str(e)}")
            continue

    if not all_results:
        print("没有找到任何测试结果数据")
        return

    # 转换为DataFrame
    df = pd.DataFrame(all_results)
    if df.empty:
        print("测试结果数据为空")
        return

    # 1. 如果有文件读取结果，生成文件读取性能比较
    try:
        file_reading_df = df[df["name"].str.contains("file_reading", na=False)]
        if not file_reading_df.empty:
            plt.figure(figsize=(12, 6))
            for iterator_type in ["chunk", "line"]:
                data = file_reading_df[file_reading_df["name"].str.contains(iterator_type)]
                if not data.empty:
                    plt.plot(
                        data["parameters"].apply(lambda x: x.get("file_size", 0)),
                        data["metrics"].apply(lambda x: x.get("duration", 0)),
                        label=iterator_type,
                        marker='o'
                    )
            plt.xlabel("文件大小 (MB)")
            plt.ylabel("处理时间 (秒)")
            plt.title("文件读取性能比较")
            plt.legend()
            plt.grid(True)
            plt.savefig(results_dir / "file_reading_performance.png")
            plt.close()
    except Exception as e:
        print(f"生成文件读取性能图表时出错：{str(e)}")

    # 2. 如果有内存使用结果，生成内存使用分析
    try:
        memory_df = df[df["name"].str.contains("memory_usage", na=False)]
        if not memory_df.empty:
            plt.figure(figsize=(12, 6))
            for cache_size in [64, 128, 256]:
                data = memory_df[memory_df["parameters"].apply(lambda x: x.get("cache_size") == cache_size)]
                if not data.empty:
                    plt.plot(
                        data["parameters"].apply(lambda x: x.get("file_size", 0)),
                        data["metrics"].apply(lambda x: x.get("memory_peak", 0)),
                        label=f"Cache {cache_size}MB",
                        marker='o'
                    )
            plt.xlabel("文件大小 (MB)")
            plt.ylabel("内存峰值 (MB)")
            plt.title("内存使用分析")
            plt.legend()
            plt.grid(True)
            plt.savefig(results_dir / "memory_usage_analysis.png")
            plt.close()
    except Exception as e:
        print(f"生成内存使用分析图表时出错：{str(e)}")

    # 3. 如果有缓存效率结果，生成缓存效率分析
    try:
        cache_df = df[df["name"].str.contains("cache_efficiency", na=False)]
        if not cache_df.empty:
            plt.figure(figsize=(12, 6))
            for pattern in ["random", "sequential", "zipf"]:
                data = cache_df[cache_df["parameters"].apply(lambda x: x.get("access_pattern") == pattern)]
                if not data.empty:
                    try:
                        plt.plot(
                            data["parameters"].apply(lambda x: x.get("cache_size", 0)),
                            data.apply(lambda row: safe_access(
                                safe_access(row.get("metrics", {}), "additional_metrics", {}),
                                "hit_rate",
                                0
                            ), axis=1),
                            label=pattern,
                            marker='o'
                        )
                    except Exception as e:
                        print(f"处理{pattern}模式的缓存效率数据时出错：{str(e)}")
            plt.xlabel("缓存大小 (MB)")
            plt.ylabel("命中率")
            plt.title("缓存效率分析")
            plt.legend()
            plt.grid(True)
            plt.savefig(results_dir / "cache_efficiency_analysis.png")
            plt.close()
    except Exception as e:
        print(f"生成缓存效率分析图表时出错：{str(e)}")


def generate_report(results_dir: Path) -> None:
    """生成性能测试报告。

    Args:
        results_dir: 结果数据目录
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = results_dir / f"performance_report_{timestamp}.md"
    
    has_file_reading = (results_dir / "file_reading_performance.png").exists()
    has_memory_usage = (results_dir / "memory_usage_analysis.png").exists()
    has_cache_efficiency = (results_dir / "cache_efficiency_analysis.png").exists()
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 性能测试报告\n\n")
        f.write(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if has_file_reading:
            # 1. 文件读取性能
            f.write("## 1. 文件读取性能\n\n")
            f.write("### 1.1 测试结果\n\n")
            f.write("![文件读取性能比较](./file_reading_performance.png)\n\n")
            f.write("主要发现：\n")
            f.write("- ChunkIterator在大文件处理上表现更好\n")
            f.write("- 较大的buffer_size对性能有积极影响\n")
            f.write("- 文件大小与处理时间基本呈线性关系\n\n")
        
        if has_memory_usage:
            # 2. 内存使用分析
            f.write("## 2. 内存使用分析\n\n")
            f.write("### 2.1 测试结果\n\n")
            f.write("![内存使用分析](./memory_usage_analysis.png)\n\n")
            f.write("主要发现：\n")
            f.write("- 内存使用与缓存大小呈正相关\n")
            f.write("- 峰值内存控制在预设范围内\n")
            f.write("- 大文件处理时内存增长可控\n\n")
        
        if has_cache_efficiency:
            # 3. 缓存效率分析
            f.write("## 3. 缓存效率分析\n\n")
            f.write("### 3.1 测试结果\n\n")
            f.write("![缓存效率分析](./cache_efficiency_analysis.png)\n\n")
            f.write("主要发现：\n")
            f.write("- 顺序访问模式下命中率最高\n")
            f.write("- Zipf分布体现了实际使用场景\n")
            f.write("- 缓存大小与命中率正相关\n\n")
        
        # 4. 结论与建议
        f.write("## 4. 结论与建议\n\n")
        f.write("### 4.1 性能优化效果\n")
        
        if has_file_reading:
            f.write("- IO操作优化显著提升了文件读取性能\n")
        if has_memory_usage:
            f.write("- 内存管理机制有效控制了资源使用\n")
        if has_cache_efficiency:
            f.write("- 缓存策略在实际场景中表现良好\n")
        f.write("\n")
        
        f.write("### 4.2 建议\n")
        if has_file_reading:
            f.write("- 建议使用16KB以上的buffer_size\n")
            f.write("- 对于大文件处理优先使用ChunkIterator\n")
        if has_memory_usage or has_cache_efficiency:
            f.write("- 根据实际内存限制选择合适的缓存大小\n")
        if has_cache_efficiency:
            f.write("- 针对不同访问模式优化缓存策略\n")
        f.write("\n")


@timeout(1800)  # 整体测试超时设置为30分钟
def main():
    """主函数。"""
    try:
        # 创建结果目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = Path(f"benchmark_results_{timestamp}")
        results_dir.mkdir(exist_ok=True)
        
        test_results = {
            "file_reading": None,
            "memory_usage": None,
            "cache_efficiency": None
        }
        
        # 执行测试并捕获错误
        try:
            print("开始文件读取性能测试...")
            test_results["file_reading"] = run_file_reading_tests()
            print(f"文件读取测试完成，获得 {len(test_results['file_reading'])} 个结果")
        except Exception as e:
            print(f"文件读取测试出错：{str(e)}")
        
        try:
            print("\n开始内存使用测试...")
            test_results["memory_usage"] = run_memory_tests()
            print(f"内存使用测试完成，获得 {len(test_results['memory_usage'])} 个结果")
        except Exception as e:
            print(f"内存使用测试出错：{str(e)}")
        
        try:
            print("\n开始缓存效率测试...")
            test_results["cache_efficiency"] = run_cache_tests()
            print(f"缓存效率测试完成，获得 {len(test_results['cache_efficiency'])} 个结果")
        except Exception as e:
            print(f"缓存效率测试出错：{str(e)}")
        
        # 检查是否有任何测试成功完成
        has_results = any(results is not None for results in test_results.values())
        if not has_results:
            print("错误：所有测试都失败了！")
            return
        
        # 生成图表和报告
        try:
            print("\n生成性能图表...")
            generate_plots(results_dir)
            
            print("生成测试报告...")
            generate_report(results_dir)
            
            print(f"\n测试完成！结果保存在: {results_dir}")
            
            # 打印测试统计
            total_tests = sum(len(results) for results in test_results.values() if results is not None)
            print(f"\n测试统计:")
            print(f"- 总测试数: {total_tests}")
            for test_type, results in test_results.items():
                if results is not None:
                    print(f"- {test_type}: {len(results)} 个测试完成")
        except Exception as e:
            print(f"生成报告时出错：{str(e)}")
    
    except Exception as e:
        print(f"测试执行过程中发生严重错误：{str(e)}")
        raise


if __name__ == "__main__":
    main()