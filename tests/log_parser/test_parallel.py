"""Tests for parallel processing module."""

import os
import pytest
from src.log_parser.reader.parallel import ThreadPool, TaskManager, Worker
from src.log_parser.reader.parallel.task_manager import FileChunk

def test_thread_pool_initialization():
    """Test thread pool initialization with valid and invalid worker counts."""
    # Valid worker count
    pool = ThreadPool(max_workers=4)
    assert pool.max_workers == 4
    assert not pool.is_active
    
    # Invalid worker counts
    with pytest.raises(ValueError):
        ThreadPool(max_workers=0)
    with pytest.raises(ValueError):
        ThreadPool(max_workers=5)

def test_thread_pool_lifecycle():
    """Test thread pool start/stop lifecycle."""
    pool = ThreadPool(max_workers=2)
    
    # Test start
    pool.start()
    assert pool.is_active
    
    # Test stop
    pool.stop()
    assert not pool.is_active

def test_task_manager_file_splitting():
    """Test task manager's file splitting functionality."""
    # Create a temporary test file
    test_file = "test_file.txt"
    content = b"test" * 1024  # 4KB of data
    with open(test_file, "wb") as f:
        f.write(content)
    
    try:
        manager = TaskManager(chunk_size=1024)  # 1KB chunks
        chunk_count = manager.prepare_file_tasks(test_file)
        
        assert chunk_count == 4
        
        # Verify chunks
        chunks = []
        while True:
            chunk = manager.get_next_task()
            if not chunk:
                break
            chunks.append(chunk)
        
        assert len(chunks) == 4
        assert all(isinstance(chunk, FileChunk) for chunk in chunks)
        assert chunks[0].chunk_size == 1024
    finally:
        os.remove(test_file)

def test_worker_processing():
    """Test worker's chunk processing capability."""
    def mock_processor(chunk: FileChunk) -> bytes:
        return b"processed"
    
    worker = Worker(worker_id=1)
    worker.set_processor(mock_processor)
    
    chunk = FileChunk(
        file_path="test.txt",
        start_pos=0,
        chunk_size=1024,
        chunk_id=1
    )
    
    assert not worker.is_busy
    result = worker.process_chunk(chunk)
    assert result == b"processed"
    assert not worker.is_busy

def test_integrated_parallel_processing():
    """Test integrated parallel processing workflow."""
    # Create test file
    test_file = "test_integrated.txt"
    content = b"test" * 1024 * 1024  # 4MB of data
    with open(test_file, "wb") as f:
        f.write(content)
    
    try:
        # Initialize components
        pool = ThreadPool(max_workers=2)
        manager = TaskManager(chunk_size=1024 * 1024)  # 1MB chunks
        
        # Prepare tasks
        chunk_count = manager.prepare_file_tasks(test_file)
        assert chunk_count == 4
        
        # Start processing
        pool.start()
        
        def process_chunk(chunk: FileChunk) -> bytes:
            with open(chunk.file_path, "rb") as f:
                f.seek(chunk.start_pos)
                return f.read(chunk.chunk_size)
        
        # Submit all chunks for processing
        futures = []
        while True:
            chunk = manager.get_next_task()
            if not chunk:
                break
            futures.append(pool.submit(process_chunk, chunk))
        
        # Collect results
        for future in futures:
            result = future.result()
            assert len(result) > 0
        
        pool.stop()
        
        # 确保所有文件句柄都已关闭
        import gc
        gc.collect()
    finally:
        # 多次尝试删除文件
        for _ in range(3):
            try:
                os.remove(test_file)
                break
            except PermissionError:
                import time
                time.sleep(0.1)

if __name__ == "__main__":
    pytest.main([__file__])