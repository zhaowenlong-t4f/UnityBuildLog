"""Worker implementation for processing file chunks."""

from typing import Optional, Callable
import logging
from .task_manager import FileChunk

logger = logging.getLogger(__name__)

class Worker:
    """Worker class for processing file chunks."""
    
    def __init__(self, worker_id: int):
        """Initialize worker.
        
        Args:
            worker_id (int): Unique identifier for the worker
        """
        self.worker_id = worker_id
        self._current_task: Optional[FileChunk] = None
        self._processor: Optional[Callable[[FileChunk], bytes]] = None
        
    def process_chunk(self, chunk: FileChunk) -> bytes:
        """Process a file chunk.
        
        Args:
            chunk (FileChunk): Chunk of file to process
            
        Returns:
            bytes: Processed data
            
        Raises:
            RuntimeError: If no processor is set
            IOError: If file reading fails
        """
        if not self._processor:
            raise RuntimeError("No processor function set")
            
        self._current_task = chunk
        try:
            result = self._processor(chunk)
            logger.debug(f"Worker {self.worker_id} processed chunk {chunk.chunk_id}")
            return result
        finally:
            self._current_task = None
            
    def set_processor(self, processor: Callable[[FileChunk], bytes]):
        """Set the processor function for this worker.
        
        Args:
            processor: Function that takes a FileChunk and returns processed bytes
        """
        self._processor = processor
        
    @property
    def is_busy(self) -> bool:
        """Check if worker is currently processing a task."""
        return self._current_task is not None
        
    @property
    def current_task(self) -> Optional[FileChunk]:
        """Get current task being processed."""
        return self._current_task