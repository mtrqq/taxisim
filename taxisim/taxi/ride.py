import enum
import uuid
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Optional

import transitions

from taxisim import ticks
from taxisim.callback import Callback

if TYPE_CHECKING:
    from taxisim.human import Human
    from taxisim.point import Point
    from taxisim.taxi.car import Car


class State(enum.IntEnum):
    Pending = enum.auto()
    CarAssigned = enum.auto()
    InProgress = enum.auto()
    Finished = enum.auto()
    Cancelled = enum.auto()


class Ride:
    """
    States:
    * Pending
    * CarAssigned
    * InProgress
    * Finished

    Pending -> CarAssigned | assign_car(car)
    CarAssigned -> InProgress | pick_up(), on_assigned
    InProgress -> Finished | finish(), on_finished
    [Pending, CarAssigned] -> Cancelled | cancel()
    """

    def __init__(
        self,
        source: "Point",
        dest: "Point",
        *,
        passenger: "Human",
        id: uuid.UUID | None = None,
        on_car_assigned: Callable[["Car"], None] | None = None,
        on_car_arrived: Callable[[], None] | None = None,
        on_ride_finished: Callable[[], None] | None = None,
        on_ride_cancelled: Callable[[], None] | None = None,
    ) -> None:
        self.id: uuid.UUID = id or uuid.uuid4()
        self.source = source
        self.dest = dest
        self.passenger = passenger
        self.car: Optional["Car"] = None

        self.created_at: int = ticks.get()
        self.started_at: int | None = None
        self.done_at: int | None = None

        self.on_car_assigned = Callback.from_optional(on_car_assigned)
        self.on_car_arrived = Callback.from_optional(on_car_arrived)
        self.on_ride_finished = Callback.from_optional(on_ride_finished)
        self.on_ride_cancelled = Callback.from_optional(on_ride_cancelled)
        self._smachine = transitions.Machine(
            self,
            states=State,
            initial=State.Pending,
            transitions=[
                {
                    "trigger": "assign_car",
                    "source": State.Pending,
                    "dest": State.CarAssigned,
                    "after": self.on_car_assigned,
                },
                {
                    "trigger": "pick_up",
                    "source": State.CarAssigned,
                    "dest": State.InProgress,
                    "before": [self._mark_started, self.on_car_arrived],
                },
                {
                    "trigger": "finish",
                    "source": State.InProgress,
                    "dest": State.Finished,
                    "after": [self._mark_done, self.on_ride_finished],
                },
                {
                    "trigger": "cancel",
                    "source": [State.Pending, State.CarAssigned],
                    "dest": State.Cancelled,
                    "after": [self._mark_done, self.on_ride_cancelled],
                },
            ],
        )

    def _mark_started(self, *_: Any) -> None:
        self.started_at = ticks.get()

    def _mark_done(self, *_: Any) -> None:
        self.done_at = ticks.get()

    def set_environment(self, car: Optional["Car"] = None):
        if car is not None:
            self.car = car

    @property
    def is_started(self) -> bool:
        return self.state != State.Pending

    @property
    def is_done(self) -> bool:
        return self.is_cancelled or self.is_finished

    @property
    def is_finished(self) -> bool:
        return self.state == State.Finished

    @property
    def is_cancelled(self) -> bool:
        return self.state == State.Cancelled

    @property
    def wait_time(self) -> int:
        if not self.is_done:
            return ticks.get() - self.started_at

        if self.is_cancelled:
            return self.done_at - self.created_at
        else:
            return self.started_at - self.created_at

    @property
    def duration(self) -> int:
        return self.done_at - self.created_at
