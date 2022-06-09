import random
from typing import Callable

CarWaiter = Callable[[int, float], bool]
StatusChecker = Callable[[], bool]


def wait_n_ticks(n):
    def should_wait(tick, _):
        return tick <= n

    return should_wait


def random_checker(chance):
    def check():
        return random.random() <= chance

    return check
