import enum
import uuid
from typing import TYPE_CHECKING
from typing import Callable
from typing import Optional

import transitions

from taxisim.callback import Callback

if TYPE_CHECKING:
    from taxisim.point import Point
    from taxisim.taxi.ride import Ride


class State(enum.IntEnum):
    WaitRide = enum.auto()
    RideToSource = enum.auto()
    WaitPassenger = enum.auto()
    RideToDest = enum.auto()


class Car:
    """
    States:
    * WaitOrder
    * Ride

    WaitOrder -> Ride | accept_ride(ride)
    Ride -> WaitOrder | ride_finished
    """

    def __init__(
        self,
        pos: "Point",
        speed: float,
        *,
        id: uuid.UUID | None = None,
        on_ride_accepted: Callable[["Ride"], None] | None = None,
        on_ride_started: Callable[[], None] | None = None,
        on_waiting_passenger: Callable[[], None] | None = None,
        on_ride_finished: Callable[[], None] | None = None,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.speed = speed
        self.pos = pos
        self.ride: Optional["Ride"] = None

        self.on_ride_accepted = Callback.from_optional(on_ride_accepted)
        self.on_waiting_passenger = Callback.from_optional(on_waiting_passenger)
        self.on_ride_started = Callback.from_optional(on_ride_finished)
        self.on_ride_finished = Callback.from_optional(on_ride_finished)
        self._smachine = transitions.Machine(
            self,
            states=State,
            initial=State.WaitRide,
            transitions=[
                {
                    "trigger": "accept_ride",
                    "source": State.WaitRide,
                    "dest": State.RideToSource,
                    "before": self._assign_ride,
                    "after": self.on_ride_accepted,
                },
                {
                    "trigger": "arrive_to_source",
                    "source": State.RideToSource,
                    "dest": State.WaitPassenger,
                    "after": [self._notify_passenger, self.on_waiting_passenger],
                },
                {
                    "trigger": "pick_up_passenger",
                    "source": State.WaitPassenger,
                    "dest": State.RideToDest,
                    "after": self.on_ride_started,
                },
                {
                    "trigger": "cancel_ride",
                    "source": [
                        State.RideToSource,
                        State.RideToDest,
                        State.WaitPassenger,
                    ],
                    "dest": State.WaitRide,
                    "before": [self._clear_ride],
                    "after": self.on_ride_finished,
                },
                {
                    "trigger": "arrive_to_dest",
                    "source": State.RideToDest,
                    "dest": State.WaitRide,
                    "before": [self._finish_ride, self._clear_ride],
                    "after": self.on_ride_finished,
                },
            ],
        )

    def _assign_ride(self, ride: "Ride") -> None:
        self.ride = ride

    def _finish_ride(self) -> None:
        self.ride.finish()

    def _notify_passenger(self) -> None:
        if not self.ride.is_cancelled:
            self.ride.car_arrived()

    def _clear_ride(self) -> None:
        self.ride = None

    @property
    def is_in_ride(self) -> bool:
        return self.state == State.RideToDest

    @property
    def is_free(self) -> bool:
        return self.state == State.WaitRide

    def __repr__(self) -> str:
        return f"Car(pos={self.pos}, state={self.state.name})"
