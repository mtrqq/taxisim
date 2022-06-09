from typing import Callable
from typing import Generic
from typing import ParamSpec

P = ParamSpec("P")


class Callback(Generic[P]):
    def __init__(self, *funcs):
        self.funcs = list(funcs)

    @classmethod
    def from_optional(cls, *funcs):
        return cls(*filter(None, funcs))

    def subscribe(self, *funcs):
        self.funcs.extend(funcs)

    def __call__(self, *args, **kwargs):
        for func in self.funcs:
            func(*args, **kwargs)
