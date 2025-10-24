"""Task manager for handling parallel file reading tasks."""

from typing import List, Optional, Tuple
import os
from dataclasses import dataclass
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)

@dataclass
class FileChunk:
    """Represents a chunk of file to be processed."""
    file_path: str
    start_pos: int
    chunk_size: int
    chunk_id: int

class TaskManager:
    """Manages the distribution and tracking of file reading tasks."""
    
    def __init__(self, chunk_size: int = 1024 * 1024):  # 1MB default chunk size
        """Initialize task manager.
        
        Args:
            chunk_size (int): Size of each file chunk in bytes
        """
        self._chunk_size = chunk_size
        self._task_queue: Queue[FileChunk] = Queue()
        self._results: List[Tuple[int, bytes]] = []
        
    def prepare_file_tasks(self, file_path: str) -> int:
        """Split file into chunks and prepare tasks.
        
        Args:
            file_path (str): Path to the file to be processed
            
        Returns:
            int: Number of chunks created
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_size = os.path.getsize(file_path)
        chunk_count = (file_size + self._chunk_size - 1) // self._chunk_size
        
        for i in range(chunk_count):
            start_pos = i * self._chunk_size
            chunk = FileChunk(
                file_path=file_path,
                start_pos=start_pos,
                chunk_size=min(self._chunk_size, file_size - start_pos),
                chunk_id=i
            )
            self._task_queue.put(chunk)
            
        logger.info(f"Prepared {chunk_count} chunks for file: {file_path}")
        return chunk_count
    
    def get_next_task(self) -> Optional[FileChunk]:
        """Get next available task from queue.
        
        Returns:
            Optional[FileChunk]: Next task or None if queue is empty
        """
        try:
            return self._task_queue.get_nowait()
        except Empty:
            return None
            
    def add_result(self, chunk_id: int, data: bytes):
        """Add processed chunk result.
        
        Args:
            chunk_id (int): ID of the processed chunk
            data (bytes): Processed data
        """
        self._results.append((chunk_id, data))
        
    def get_ordered_results(self) -> bytes:
        """Get results ordered by chunk ID.
        
        Returns:
            bytes: Combined results in correct order
        """
        self._results.sort(key=lambda x: x[0])
        return b''.join(chunk[1] for chunk in self._results)
        
    def clear(self):
        """Clear all tasks and results."""
        while not self._task_queue.empty():
            self._task_queue.get()
        self._results.clear()