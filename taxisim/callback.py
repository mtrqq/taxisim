from typing import Any, Callable, Generic, Iterable, Optional, ParamSpec

P = ParamSpec('P')
P2 = ParamSpec('P2')

def do_nothing(*args: Any, **kwargs: Any) -> None:
    pass

def combine_funcs(*functions: Iterable[Callable[P2, None]]) -> Callable[P2, None]:
    def combined_wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        for fun in functions:
            fun(*args, **kwargs)
        
        return combined_wrapper

class Callback(Generic[P]):    
    def __init__(self, fun: Callable[P, None]) -> None:
        self.fun = fun

    @classmethod
    def from_multiple(cls, *functions: Iterable[Callable[P, None]]) -> "Callback[P]":
        return cls(combine_funcs(functions))

    @classmethod
    def from_optional(cls, fun: Callable[P, None] | None) -> "Callback[P]" | "Callback[...]":
        if fun is None:
            return cls.empty()
        
        return cls(fun)

    @classmethod
    def empty(cls) -> "Callback[...]":
        return cls(do_nothing)

    def combine(self, *functions: Iterable[Callable[P, None]]) -> None:
        self.fun = combine_funcs(self.fun, *functions)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        return self.fun(*args, **kwargs)

