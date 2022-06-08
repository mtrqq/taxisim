import enum
from typing import Callable, Optional
import uuid
from taxisim.callback import Callback

from taxisim.point import Point
from taxisim.taxi.ride import Ride

class State:
    WaitRide: enum.IntEnum
    PickupPassenger: enum.IntEnum
    RideToDest: enum.IntEnum

class Car:
    state: State
    id: uuid.UUID
    speed: float
    pos: Point
    ride: Optional[Ride]
    on_ride_accepted: Callback[[Ride]]
    on_passenger_picked_up: Callback[[]]
    on_ride_finished: Callback[[]]

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
    def picked_up(self) -> None: ...
    def finish_ride(self) -> None: ...
    @property
    def is_in_ride(self) -> bool: ...
    @property
    def is_free(self) -> bool: ...
