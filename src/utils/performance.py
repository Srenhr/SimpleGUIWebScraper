# src/utils/performance.py
import time
import logging
from functools import wraps
from typing import Callable, Any

def measure_performance(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logging.debug(f"{func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logging.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
            raise
    return wrapper