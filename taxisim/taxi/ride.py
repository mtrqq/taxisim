import enum
import uuid
from typing import TYPE_CHECKING
from typing import Callable
from typing import Optional

import transitions

if TYPE_CHECKING:
    from taxisim.human import Human
    from taxisim.point import Point
    from taxisim.taxi.car import Car


class State(enum.Enum):
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
        self.smachine = transitions.Machine(
            self,
            states=State,
            initial=State.Pending,
            transitions=[
                {
                    "trigger": "assign_car",
                    "source": State.Pending,
                    "dest": State.CarAssigned,
                    "after": on_car_assigned or None,
                },
                {
                    "trigger": "pick_up",
                    "source": State.CarAssigned,
                    "dest": State.InProgress,
                    "before": on_car_arrived or None,
                },
                {
                    "trigger": "finish",
                    "source": State.InProgress,
                    "dest": State.Finished,
                    "after": on_ride_finished or None,
                },
                {
                    "trigger": "cancel",
                    "source": [State.Pending, State.CarAssigned],
                    "dest": State.Cancelled,
                    "after": on_ride_cancelled or None,
                },
            ],
        )

    def set_environment(self, car: Optional["Car"] = None):
        if car is not None:
            self.car = car

    @property
    def is_started(self) -> bool:
        return self.state != State.Pending

    @property
    def is_done(self) -> bool:
        return self.state in [State.Cancelled, State.Finished]
