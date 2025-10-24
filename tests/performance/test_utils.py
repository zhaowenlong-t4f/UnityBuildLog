"""超时装饰器和工具函数。"""

import time
import threading
from functools import wraps
from typing import Callable, Any, Optional


class TimeoutError(Exception):
    """超时错误。"""
    pass


def timeout(seconds: int) -> Callable:
    """超时装饰器。

    Args:
        seconds: 超时秒数

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = []
            error = []
            
            def target() -> None:
                try:
                    result.append(func(*args, **kwargs))
                except Exception as e:
                    error.append(e)
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                raise TimeoutError(f"函数执行超过{seconds}秒")
            
            if error:
                raise error[0]
            
            return result[0] if result else None
        
        return wrapper
    
    return decorator