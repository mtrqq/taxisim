from collections import defaultdict
from typing import Hashable

_TICKS = defaultdict(int)


def get(tid=None):
    return _TICKS[tid]


def increment_by(by, tid=None):
    _TICKS[tid] += by
    return _TICKS[tid]


def increment(tid=None):
    return increment_by(1)


def reset(tid=None):
    _TICKS[tid] = 0
