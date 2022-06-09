from typing import Callable
from typing import Generic
from typing import ParamSpec

P = ParamSpec("P")


class Callback(Generic[P]):
    def __init__(self, *funcs: Callable[P, None]) -> None:
        self.funcs = list(funcs)

    @classmethod
    def from_optional(cls, *funcs: Callable[P, None] | None) -> "Callback[P]":
        return cls(*filter(None, funcs))

    def subscribe(self, *funcs: Callable[P, None]) -> None:
        self.funcs.extend(funcs)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        for func in self.funcs:
            func(*args, **kwargs)
