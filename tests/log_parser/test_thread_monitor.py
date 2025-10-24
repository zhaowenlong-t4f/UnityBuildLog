"""线程性能监控测试模块。"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from pathlib import Path
from src.log_parser.reader.monitoring.thread_monitor import ThreadMonitor


def test_thread_monitor_basic():
    """测试线程监控器的基本功能。"""
    monitor = ThreadMonitor()
    thread_id = monitor.register_thread()

    # 测试任务跟踪
    monitor.start_task(thread_id, "test_task_1")
    time.sleep(0.1)  # 模拟任务执行
    monitor.end_task(thread_id, "test_task_1", success=True)

    # 获取统计信息
    stats = monitor.get_thread_stats(thread_id)
    assert stats is not None
    assert stats["thread_id"] == thread_id
    assert stats["total_tasks"] == 1
    assert stats["completed_tasks"] == 1
    assert stats["failed_tasks"] == 0
    assert stats["success_rate"] == 1.0
    assert stats["avg_task_time"] > 0


def test_thread_monitor_multiple_threads():
    """测试多线程监控。"""
    monitor = ThreadMonitor()
    thread_ids = []

    def worker():
        thread_id = monitor.register_thread()
        thread_ids.append(thread_id)
        for i in range(3):
            task_id = f"task_{thread_id}_{i}"
            monitor.start_task(thread_id, task_id)
            time.sleep(0.05)  # 模拟任务执行
            monitor.end_task(thread_id, task_id, success=True)
        return thread_id

    # 使用线程池执行任务
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交任务到线程池
        futures = [executor.submit(worker) for _ in range(3)]

        # 等待所有任务完成，带超时
        try:
            for future in as_completed(futures, timeout=3):
                thread_id = future.result()
        except TimeoutError:
            pytest.fail("Thread execution timed out")

    # 验证每个线程的统计信息
    all_stats = monitor.get_all_stats()
    assert len(all_stats) == 3

    for thread_id in thread_ids:
        stats = all_stats[thread_id]
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 3
        assert stats["failed_tasks"] == 0
        assert stats["success_rate"] == 1.0


def test_thread_monitor_failed_tasks():
    """测试失败任务的监控。"""
    monitor = ThreadMonitor()
    thread_id = monitor.register_thread()

    # 测试成功和失败的任务
    monitor.start_task(thread_id, "success_task")
    time.sleep(0.05)
    monitor.end_task(thread_id, "success_task", success=True)

    monitor.start_task(thread_id, "failed_task")
    time.sleep(0.05)
    monitor.end_task(thread_id, "failed_task", success=False)

    # 验证统计信息
    stats = monitor.get_thread_stats(thread_id)
    assert stats["total_tasks"] == 2
    assert stats["completed_tasks"] == 1
    assert stats["failed_tasks"] == 1
    assert stats["success_rate"] == 0.5


@pytest.mark.timeout(5)  # 5秒超时
def test_thread_monitor_performance_summary():
    """测试性能摘要生成。"""
    monitor = ThreadMonitor()
    thread_ids = []
    worker_thread_ids = []

    def worker():
        # 确保在当前工作线程中也注册
        worker_thread_id = monitor.register_thread()
        worker_thread_ids.append(worker_thread_id)
        for j in range(2):
            task_id = f"task_{worker_thread_id}_{j}"
            monitor.start_task(worker_thread_id, task_id)
            time.sleep(0.05)
            monitor.end_task(worker_thread_id, task_id, success=(j % 2 == 0))
        return worker_thread_id

    # 使用线程池执行任务
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交任务到线程池
        futures = [executor.submit(worker) for _ in range(3)]

        # 等待所有任务完成，带超时
        try:
            for future in as_completed(futures, timeout=3):
                thread_id = future.result()
                thread_ids.append(thread_id)
        except TimeoutError:
            pytest.fail("Thread execution timed out")

    # 获取并验证性能摘要
    summary = monitor.get_performance_summary()
    assert summary["active_threads"] == 3
    assert summary["total_tasks"] == 6
    assert summary["completed_tasks"] == 3
    assert summary["failed_tasks"] == 3
    assert abs(summary["success_rate"] - 0.5) < 0.01
    assert "uptime_seconds" in summary
    assert "total_cpu_percent" in summary
    assert "total_memory_mb" in summary