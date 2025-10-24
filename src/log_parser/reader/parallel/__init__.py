"""
Parallel processing module for log file reading.
This module provides thread pool implementation for parallel log file processing.
"""

from .thread_pool import ThreadPool
from .task_manager import TaskManager
from .worker import Worker

__all__ = ['ThreadPool', 'TaskManager', 'Worker']