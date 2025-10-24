"""Tests for parallel chunk iterator."""

import os
import pytest
from pathlib import Path
from src.log_parser.reader.base import ReaderContext
from src.log_parser.reader.file_handlers.text_handler import TextFileHandler
from src.log_parser.reader.parallel.chunk_iterator import ParallelChunkIterator

def test_parallel_chunk_iterator(tmp_path: Path):
    """Test parallel chunk iterator functionality."""
    # 创建测试文件
    file_path = tmp_path / "test.txt"
    content = b"test" * 1024 * 1024  # 4MB data
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 设置上下文和文件处理器
    context = ReaderContext(
        file_path=file_path,
        chunk_size=1024 * 1024  # 1MB chunks
    )
    handler = TextFileHandler(context)
    
    # 创建并测试迭代器
    iterator = ParallelChunkIterator(context, handler, max_workers=2)
    
    # 读取所有块并验证
    chunks = list(iterator)
    assert len(chunks) == 4  # 应该有4个1MB的块
    
    # 验证内容
    combined_content = b"".join(chunks)
    assert combined_content == content
    
    # 测试重置功能
    iterator.reset()
    new_chunks = list(iterator)
    assert len(new_chunks) == 4
    assert b"".join(new_chunks) == content
    
    # 关闭迭代器
    iterator.close()

def test_parallel_chunk_iterator_empty_file(tmp_path: Path):
    """Test parallel chunk iterator with empty file."""
    file_path = tmp_path / "empty.txt"
    file_path.touch()
    
    context = ReaderContext(file_path=file_path)
    handler = TextFileHandler(context)
    iterator = ParallelChunkIterator(context, handler)
    
    chunks = list(iterator)
    assert len(chunks) == 0
    iterator.close()

def test_parallel_chunk_iterator_small_file(tmp_path: Path):
    """Test parallel chunk iterator with file smaller than chunk size."""
    file_path = tmp_path / "small.txt"
    content = b"small file content"
    with open(file_path, "wb") as f:
        f.write(content)
    
    context = ReaderContext(
        file_path=file_path,
        chunk_size=1024 * 1024  # 1MB chunks
    )
    handler = TextFileHandler(context)
    iterator = ParallelChunkIterator(context, handler)
    
    chunks = list(iterator)
    assert len(chunks) == 1
    assert chunks[0] == content
    iterator.close()

def test_parallel_chunk_iterator_error_handling(tmp_path: Path):
    """Test parallel chunk iterator error handling."""
    # 创建测试文件
    file_path = tmp_path / "test.txt"
    content = b"test" * 1024 * 1024
    with open(file_path, "wb") as f:
        f.write(content)
    
    context = ReaderContext(file_path=file_path)
    handler = TextFileHandler(context)
    iterator = ParallelChunkIterator(context, handler)
    
    # 读取一次
    chunks = list(iterator)
    assert len(chunks) > 0
    
    # 关闭迭代器并等待文件句柄释放
    iterator.close()
    import time
    time.sleep(0.1)  # 等待文件句柄完全释放
    
    # 删除文件后尝试重置
    os.remove(file_path)
    with pytest.raises(FileNotFoundError):
        iterator.reset()