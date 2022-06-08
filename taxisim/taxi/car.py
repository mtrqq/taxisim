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
    PickupPassenger = enum.auto()
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
        on_passenger_picked_up: Callable[[], None] | None = None,
        on_ride_finished: Callable[[], None] | None = None,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.speed = speed
        self.pos = pos
        self.ride: Optional["Ride"] = None

        self.on_ride_accepted = Callback.from_optional(on_ride_accepted)
        self.on_passenger_picked_up = Callback.from_optional(on_passenger_picked_up)
        self.on_ride_finished = Callback.from_optional(on_ride_finished)
        self._smachine = transitions.Machine(
            self,
            states=State,
            initial=State.WaitRide,
            transitions=[
                {
                    "trigger": "accept_ride",
                    "source": State.WaitRide,
                    "dest": State.PickupPassenger,
                    "after": self.on_ride_accepted,
                },
                {
                    "trigger": "picked_up",
                    "source": State.PickupPassenger,
                    "dest": State.RideToDest,
                    "after": self.on_ride_accepted,
                },
                {
                    "trigger": "ride_finished",
                    "source": State.RideToDest,
                    "dest": State.WaitRide,
                    "after": self.on_ride_finished,
                },
            ],
        )

    def set_environment(self, ride: Optional["Ride"] = None) -> None:
        self.ride = ride

    @property
    def is_in_ride(self) -> bool:
        return self.state == State.RideToDest

    @property
    def is_free(self) -> bool:
        return self.state == State.WaitRide
