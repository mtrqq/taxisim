import enum
from typing import Callable, Optional
import uuid
from taxisim.callback import Callback
from taxisim.human import Human
from taxisim.point import Point
from taxisim.taxi.car import Car

class State(enum.Enum): ...

class Ride:
    state: State
    id: uuid.UUID
    source: Point
    dest: Point
    passenger: Human
    car: Optional[Car]

    created_at: int
    started_at: int
    done_at: int

    on_car_assigned: Callback[[Optional[Car]]]
    on_car_arrived: Callback[[]]
    on_ride_finished: Callback[[]]
    on_ride_cancelled: Callback[[]]

    def __init__(
        self,
        source: Point,
        dest: Point,
        *,
        passenger: Human,
        id: Optional[uuid.UUID] = ...,
        on_car_assigned: Optional[Callable[[Car], None]] = ...,
        on_car_arrived: Optional[Callable[[], None]] = ...,
        on_ride_finished: Optional[Callable[[], None]] = ...,
        on_ride_cancelled: Optional[Callable[[], None]] = ...,
    ) -> None: ...
    def assign_car(self, car: Optional[Car] = ...) -> None: ...
    def car_arrived(self) -> None: ...
    def finish(self) -> None: ...
    def cancel(self) -> None: ...
    @property
    def is_started(self) -> bool: ...
    @property
    def is_done(self) -> bool: ...
    @property
    def is_finished(self) -> bool: ...
    @property
    def is_cancelled(self) -> bool: ...
    @property
    def wait_time(self) -> int: ...
    @property
    def duration(self) -> int: ...
