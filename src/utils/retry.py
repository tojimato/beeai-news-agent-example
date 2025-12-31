"""
Retry utility with exponential backoff for resilient error handling.

Provides decorators and helper functions for retrying operations with
configurable backoff strategies and detailed error logging.
"""

import time
import functools
from typing import Callable, TypeVar, Any

from src.utils.logger import log_warning, log_error

F = TypeVar('F', bound=Callable[..., Any])

def retry_with_backoff(
    max_retries: int = 3,
    initial_wait: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
) -> Callable[[F], F]:
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        initial_wait: Initial wait time in seconds (default: 1.0).
        backoff_factor: Multiplier for wait time between retries (default: 2.0).
        jitter: Add random jitter to prevent thundering herd (default: True).
    
    Returns:
        Decorated function with automatic retry logic.
    
    Example:
        @retry_with_backoff(max_retries=3, initial_wait=2.0)
        def flaky_operation():
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            wait_time = initial_wait
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        if jitter:
                            import random
                            actual_wait = wait_time * (0.5 + random.random())
                        else:
                            actual_wait = wait_time
                        
                        log_warning(
                            f"{func.__name__} attempt {attempt + 1}/{max_retries + 1} "
                            f"failed: {str(e)}. Retrying in {actual_wait:.1f}s..."
                        )
                        time.sleep(actual_wait)
                        wait_time *= backoff_factor
                    else:
                        log_error(
                            f"{func.__name__} failed after {max_retries} retries: "
                            f"{str(e)}"
                        )
            
            raise last_exception
        
        return wrapper  # type: ignore
    
    return decorator
