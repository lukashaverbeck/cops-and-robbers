from __future__ import annotations

import time
from itertools import accumulate
from typing import Callable, Any, Iterable


def timeout_loop(finish_time: float, tolerance: float = 1.2):
    def wrapper(func: Callable[[Any, ...], None]):
        duration = 0

        def loop_function(*args, **kwargs) -> bool:
            nonlocal duration
            start = time.time()
            if finish_time - start <= tolerance * duration:
                return False

            func(*args, **kwargs)
            duration = max(time.time() - start, duration)
            return True

        return loop_function

    return wrapper


def remaining_time(finish_time: float, proportion: float):
    assert 0 <= proportion <= 1
    return finish_time - (1 - proportion) * (finish_time - time.time())


def distribute_remaining_time(finish_time: float, proportions: Iterable[float]) -> list[float]:
    return [
        remaining_time(finish_time, cumulated_relative_size)
        for cumulated_relative_size in accumulate(proportions)
    ]
