"""Thread pool implementation for parallel log file processing."""

from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, Any
from threading import Lock
import queue
import logging

logger = logging.getLogger(__name__)

class ThreadPool:
    """Thread pool manager for parallel log file processing."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize thread pool with maximum number of workers.
        
        Args:
            max_workers (int): Maximum number of worker threads (default: 4)
        """
        if max_workers <= 0 or max_workers > 4:
            raise ValueError("Worker count must be between 1 and 4")
            
        self._max_workers = max_workers
        self._pool: Optional[ThreadPoolExecutor] = None
        self._lock = Lock()
        self._task_queue = queue.Queue()
        self._active = False
        
    def start(self):
        """Start the thread pool."""
        with self._lock:
            if not self._active:
                self._pool = ThreadPoolExecutor(
                    max_workers=self._max_workers,
                    thread_name_prefix="LogReader"
                )
                self._active = True
                logger.info(f"Thread pool started with {self._max_workers} workers")
    
    def stop(self):
        """Stop the thread pool and wait for all tasks to complete."""
        with self._lock:
            if self._active and self._pool:
                self._pool.shutdown(wait=True)
                self._pool = None
                self._active = False
                logger.info("Thread pool stopped")
    
    def submit(self, fn: Callable[..., Any], *args, **kwargs) -> Optional[Any]:
        """Submit a task to the thread pool.
        
        Args:
            fn: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Future object representing the execution of the task
        
        Raises:
            RuntimeError: If thread pool is not active
        """
        if not self._active or not self._pool:
            raise RuntimeError("Thread pool is not active")
        
        return self._pool.submit(fn, *args, **kwargs)
    
    @property
    def is_active(self) -> bool:
        """Check if thread pool is active."""
        return self._active
    
    @property
    def max_workers(self) -> int:
        """Get maximum number of workers."""
        return self._max_workers