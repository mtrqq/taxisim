from collections import defaultdict
from typing import Hashable

_TICKS: dict[Hashable, int] = defaultdict(int)


def get(tid: Hashable | None = None, /) -> int:
    return _TICKS[tid]


def increment_by(by: int, /, tid: Hashable | None = None) -> int:
    _TICKS[tid] += by
    return _TICKS[tid]


def increment(tid: Hashable | None = None) -> int:
    return increment_by(1)


def reset(tid: Hashable | None = None) -> None:
    _TICKS[tid] = 0
