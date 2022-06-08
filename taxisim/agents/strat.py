import random
from typing import Callable

CarWaiter = Callable[[int, float], bool]
StatusChecker = Callable[[], bool]


def wait_n_ticks(n: int) -> CarWaiter:
    def should_wait(tick: int, _: float) -> bool:
        return tick <= n

    return should_wait


def random_checker(chance: float) -> StatusChecker:
    def check() -> bool:
        return random.random() <= chance

    return check
