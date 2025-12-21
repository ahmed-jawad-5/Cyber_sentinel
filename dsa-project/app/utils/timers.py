# app/utils/timers.py
import time
from typing import Callable, Tuple, Any

def timed(fn: Callable, *args, **kwargs) -> Tuple[Any, float]:
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    t1 = time.perf_counter()
    return result, (t1 - t0)
