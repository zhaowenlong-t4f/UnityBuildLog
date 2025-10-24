"""Tests for parallel processing optimization features."""

import pytest
from pathlib import Path
import time
from src.log_parser.reader.base import ReaderContext
from src.log_parser.reader.file_handlers.text_handler import TextFileHandler
from src.log_parser.reader.parallel.load_balancer import LoadBalancer
from src.log_parser.reader.parallel.error_handler import ErrorHandler
from src.log_parser.reader.parallel.chunk_iterator import ParallelChunkIterator

def test_load_balancer_optimization(tmp_path: Path):
    """Test load balancer's chunk size optimization."""
    # 创建负载均衡器
    balancer = LoadBalancer(initial_workers=2, max_workers=4)
    
    # 模拟不同性能的工作线程
    balancer.register_worker(1)
    balancer.register_worker(2)
    
    # 更新性能统计
    balancer.update_worker_stats(1, 1.0, 1024 * 1024)  # 1MB/s
    balancer.update_worker_stats(2, 0.5, 1024 * 1024)  # 2MB/s
    
    # 验证块大小是否根据性能差异调整
    initial_size = balancer.get_optimal_chunk_size()
    balancer.update_worker_stats(1, 2.0, 1024 * 1024)  # 更差的性能
    adjusted_size = balancer.get_optimal_chunk_size()
    
    assert adjusted_size < initial_size  # 块大小应该减小

def test_error_handler_retry_mechanism():
    """Test error handler's retry mechanism."""
    handler = ErrorHandler(max_retries=3, retry_delay=0.1)
    
    # 注册恢复处理器
    def recovery_handler(context):
        context.metadata["recovered"] = True
    
    handler.register_recovery_handler(ValueError, recovery_handler)
    
    # 测试错误处理和重试
    error = ValueError("test error")
    task_id = "test_task"
    
    # 第一次重试应该返回True
    assert handler.handle_error(error, task_id)
    
    # 验证错误上下文
    context = handler.get_error_context(task_id)
    assert context is not None
    assert context.retry_count == 0
    assert context.metadata.get("recovered") is True
    
    # 超过最大重试次数
    for _ in range(3):
        handler.handle_error(error, task_id)
    assert not handler.handle_error(error, task_id)

def test_parallel_processing_with_errors(tmp_path: Path):
    """Test parallel processing with error handling."""
    # 创建测试文件
    file_path = tmp_path / "test.txt"
    content = b"test" * 1024 * 1024  # 4MB
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 配置并创建迭代器
    context = ReaderContext(file_path=file_path, chunk_size=1024 * 1024)
    handler = TextFileHandler(context)
    iterator = ParallelChunkIterator(context, handler, max_workers=2)
    
    try:
        # 读取数据并验证
        chunks = list(iterator)
        assert len(chunks) > 0
        
        # 验证处理结果
        combined = b"".join(chunks)
        assert combined == content
        
        # 检查性能统计
        stats = iterator._reader.get_worker_stats()
        assert "workers" in stats
        assert "optimal_chunk_size" in stats
        assert len(stats["workers"]) > 0
        
    finally:
        iterator.close()

def test_parallel_processing_recovery(tmp_path: Path):
    """Test parallel processing recovery after errors."""
    # 创建测试文件
    file_path = tmp_path / "test_recovery.txt"
    content = b"test" * 1024 * 1024  # 4MB
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 配置上下文和处理器
    context = ReaderContext(file_path=file_path, chunk_size=1024 * 1024)
    handler = TextFileHandler(context)
    
    # 创建迭代器
    iterator = ParallelChunkIterator(context, handler, max_workers=2)
    
    try:
        # 第一次读取
        chunks1 = list(iterator)
        assert len(chunks1) > 0
        
        # 重置并再次读取
        iterator.reset()
        chunks2 = list(iterator)
        assert len(chunks2) == len(chunks1)
        
        # 验证数据一致性
        assert b"".join(chunks1) == b"".join(chunks2)
        
        # 检查性能统计
        stats = iterator._reader.get_worker_stats()
        assert len(stats["unhealthy_workers"]) == 0  # 不应该有不健康的工作线程
        
    finally:
        iterator.close()