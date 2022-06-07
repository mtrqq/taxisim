from typing import Callable

CarWaiter = Callable[[int, float], bool]


def wait_n_ticks(n: int) -> CarWaiter:
    def should_wait(tick: int, _: float) -> bool:
        return tick <= n

    return should_wait
