"""Error handler for parallel processing."""

from typing import Dict, Any, Optional, Type, Callable
from threading import Lock
import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Context information for error handling."""
    error_type: Type[Exception]
    error_message: str
    task_id: str
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class ErrorHandler:
    """Error handler for parallel processing tasks."""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize error handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries (will be exponential)
        """
        self._lock = Lock()
        self._max_retries = max_retries
        self._base_retry_delay = retry_delay
        self._error_counts: Dict[str, int] = {}  # task_id -> error count
        self._error_contexts: Dict[str, ErrorContext] = {}  # task_id -> context
        self._recovery_handlers: Dict[Type[Exception], Callable] = {}
        
    def register_recovery_handler(
        self,
        error_type: Type[Exception],
        handler: Callable[[ErrorContext], None]
    ) -> None:
        """Register a recovery handler for a specific error type.
        
        Args:
            error_type: Type of error to handle
            handler: Recovery handler function
        """
        with self._lock:
            self._recovery_handlers[error_type] = handler
            
    def handle_error(
        self,
        error: Exception,
        task_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Handle an error and determine if retry is needed.
        
        Args:
            error: The exception that occurred
            task_id: Identifier for the failed task
            metadata: Additional context information
            
        Returns:
            bool: True if task should be retried
        """
        with self._lock:
            # Update error counts
            current_count = self._error_counts.get(task_id, 0) + 1
            self._error_counts[task_id] = current_count
            
            # Create or update error context
            context = ErrorContext(
                error_type=type(error),
                error_message=str(error),
                task_id=task_id,
                retry_count=current_count - 1,
                metadata=metadata or {}
            )
            self._error_contexts[task_id] = context
            
            # Check if we have a recovery handler
            handler = self._recovery_handlers.get(type(error))
            if handler:
                try:
                    handler(context)
                except Exception as e:
                    logger.error(f"Recovery handler failed: {e}")
            
            # Determine if we should retry
            should_retry = current_count <= self._max_retries
            if should_retry:
                retry_delay = self._get_retry_delay(current_count)
                logger.info(
                    f"Task {task_id} will be retried in {retry_delay:.2f}s "
                    f"(attempt {current_count}/{self._max_retries})"
                )
                time.sleep(retry_delay)
            else:
                logger.warning(
                    f"Task {task_id} failed permanently after "
                    f"{current_count} attempts"
                )
                
            return should_retry
            
    def clear_error(self, task_id: str) -> None:
        """Clear error state for a task.
        
        Args:
            task_id: Task identifier
        """
        with self._lock:
            self._error_counts.pop(task_id, None)
            self._error_contexts.pop(task_id, None)
            
    def get_error_context(self, task_id: str) -> Optional[ErrorContext]:
        """Get error context for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[ErrorContext]: Error context if available
        """
        with self._lock:
            return self._error_contexts.get(task_id)
            
    def _get_retry_delay(self, retry_count: int) -> float:
        """Calculate retry delay with exponential backoff.
        
        Args:
            retry_count: Current retry attempt number
            
        Returns:
            float: Delay in seconds
        """
        return min(
            self._base_retry_delay * (2 ** (retry_count - 1)),
            30.0  # Maximum delay of 30 seconds
        )