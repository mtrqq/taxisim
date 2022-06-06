from collections import defaultdict
from typing import Hashable

_TICKS: dict[Hashable, int] = defaultdict(int)


def get(tid: Hashable | None = None, /) -> int:
    return _TICKS[tid]


def increment(tid: Hashable | None = None) -> int:
    _TICKS[tid] += 1
    return _TICKS[tid]
