from typing import Callable, Optional
import uuid
import transitions
from taxisim.callback import Callback

from taxisim.point import Point
from taxisim.taxi.ride import Ride

class State: ...

class Car:
    state: State
    id: uuid.UUID
    speed: float
    pos: Point
    on_ride_accepted: Callback[[Ride]]
    on_ride_finished: Callback[[]]
    smachine: transitions.Machine

    def __init__(
        self,
        pos: Point,
        speed: float,
        *,
        id: uuid.UUID | None = ...,
        on_ride_accepted: Callable[[Ride], None] | None = ...,
        on_ride_finished: Callable[[], None] | None = ...,
    ) -> None: ...
    def accept_ride(self, ride: Optional[Ride] = ...) -> None: ...
    def finish_ride(self) -> None: ...
    @property
    def is_in_ride(self) -> bool: ...
