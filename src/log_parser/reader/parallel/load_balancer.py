"""Load balancer for parallel processing."""

from typing import Dict, Optional, List
import time
from dataclasses import dataclass
from threading import Lock
import logging

logger = logging.getLogger(__name__)

@dataclass
class WorkerStats:
    """Worker statistics for load balancing."""
    worker_id: int
    processing_time: float = 0.0
    processed_bytes: int = 0
    error_count: int = 0
    last_active: float = 0.0
    total_tasks: int = 0
    
    @property
    def throughput(self) -> float:
        """Calculate worker's throughput in bytes per second."""
        if self.processing_time <= 0:
            return 0.0
        return self.processed_bytes / self.processing_time
    
    @property
    def error_rate(self) -> float:
        """Calculate worker's error rate."""
        if self.total_tasks <= 0:
            return 0.0
        return self.error_count / self.total_tasks
    
    @property
    def is_healthy(self) -> bool:
        """Check if worker is healthy based on error rate."""
        return self.error_rate < 0.1  # 10% error rate threshold

class LoadBalancer:
    """Load balancer for parallel processing tasks."""
    
    def __init__(self, initial_workers: int = 2, max_workers: int = 4):
        """Initialize load balancer.
        
        Args:
            initial_workers: Initial number of workers
            max_workers: Maximum number of workers allowed
        """
        self._lock = Lock()
        self._max_workers = max_workers
        self._current_workers = initial_workers
        self._worker_stats: Dict[int, WorkerStats] = {}
        self._optimal_chunk_size = 1024 * 1024  # Start with 1MB
        self._adjustment_threshold = 0.2  # 20% performance difference triggers adjustment
        
    def register_worker(self, worker_id: int) -> None:
        """Register a new worker.
        
        Args:
            worker_id: Unique identifier for the worker
        """
        with self._lock:
            if worker_id not in self._worker_stats:
                self._worker_stats[worker_id] = WorkerStats(worker_id)
                logger.info(f"Registered worker {worker_id}")
                
    def update_worker_stats(
        self,
        worker_id: int,
        processing_time: float,
        processed_bytes: int,
        had_error: bool = False
    ) -> None:
        """Update worker statistics.
        
        Args:
            worker_id: Worker identifier
            processing_time: Time taken to process task
            processed_bytes: Number of bytes processed
            had_error: Whether an error occurred
        """
        with self._lock:
            if worker_id not in self._worker_stats:
                self.register_worker(worker_id)
                
            stats = self._worker_stats[worker_id]
            stats.processing_time += processing_time
            stats.processed_bytes += processed_bytes
            stats.total_tasks += 1
            stats.last_active = time.time()
            
            if had_error:
                stats.error_count += 1
                
            self._adjust_chunk_size(stats.throughput)
            
    def get_optimal_chunk_size(self) -> int:
        """Get the current optimal chunk size.
        
        Returns:
            int: Optimal chunk size in bytes
        """
        return self._optimal_chunk_size
        
    def should_retry(self, worker_id: int, error_count: int) -> bool:
        """Determine if a failed task should be retried.
        
        Args:
            worker_id: Worker identifier
            error_count: Number of previous retry attempts
            
        Returns:
            bool: True if task should be retried
        """
        with self._lock:
            if worker_id not in self._worker_stats:
                return error_count < 3  # Default retry policy
                
            stats = self._worker_stats[worker_id]
            if not stats.is_healthy:
                logger.warning(f"Worker {worker_id} marked as unhealthy")
                return False
                
            # Implement exponential backoff
            return error_count < 3 and stats.error_rate < 0.3
            
    def get_worker_count(self) -> int:
        """Get the current recommended worker count.
        
        Returns:
            int: Recommended number of workers
        """
        with self._lock:
            return self._current_workers
            
    def _adjust_chunk_size(self, current_throughput: float) -> None:
        """Adjust chunk size based on throughput.
        
        Args:
            current_throughput: Current processing throughput
        """
        if current_throughput <= 0:
            return
            
        # Calculate average throughput excluding the current worker
        others_throughput = [
            stat.throughput
            for stat in self._worker_stats.values()
            if stat.throughput > 0 and stat.throughput != current_throughput
        ]
        
        if not others_throughput:
            return
            
        avg_throughput = sum(others_throughput) / len(others_throughput)
        
        # Adjust chunk size if there's a significant performance difference
        if abs(current_throughput - avg_throughput) / avg_throughput > self._adjustment_threshold:
            if current_throughput < avg_throughput:
                # Decrease chunk size
                self._optimal_chunk_size = max(
                    self._optimal_chunk_size // 2,
                    64 * 1024  # Minimum 64KB
                )
            else:
                # Increase chunk size
                self._optimal_chunk_size = min(
                    self._optimal_chunk_size * 2,
                    8 * 1024 * 1024  # Maximum 8MB
                )
            logger.info(f"Adjusted chunk size to {self._optimal_chunk_size}")
            
    def get_unhealthy_workers(self) -> List[int]:
        """Get list of unhealthy worker IDs.
        
        Returns:
            List[int]: List of unhealthy worker IDs
        """
        with self._lock:
            return [
                worker_id
                for worker_id, stats in self._worker_stats.items()
                if not stats.is_healthy
            ]
            
    def get_worker_health(self, worker_id: int) -> Optional[Dict[str, float]]:
        """Get health metrics for a specific worker.
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            Optional[Dict[str, float]]: Health metrics or None if worker not found
        """
        with self._lock:
            if worker_id not in self._worker_stats:
                return None
                
            stats = self._worker_stats[worker_id]
            return {
                "throughput": stats.throughput,
                "error_rate": stats.error_rate,
                "total_tasks": stats.total_tasks,
                "processed_bytes": stats.processed_bytes,
                "processing_time": stats.processing_time
            }