import enum
import uuid
from typing import TYPE_CHECKING
from typing import Callable
from typing import TypeVar

import transitions

from taxisim.callback import Callback

if TYPE_CHECKING:
    from taxisim.point import Point
    from taxisim.taxi.ride import Ride


T = TypeVar("T")


def _ensureattr(attr: T | None, name: str) -> T:
    if attr is None:
        raise RuntimeError(f"Unable to fetch {name} value")

    return attr


class State(enum.IntEnum):
    Rest = enum.auto()
    WannaParty = enum.auto()
    OrderingCar = enum.auto()
    AwaitingRide = enum.auto()
    Ride = enum.auto()
    WaitGuest = enum.auto()
    Party = enum.auto()


class Human:
    """
    States:
    * Rest
    * SeachingFriend
    * WaitGuests
    * WaitCar
    * Ride
    * Party

    at_home -> wait_car, friend.at_home -> friend.wait_guests | party
    wait_car -> ride | arrived
    ride -> party, friend.wait_guests -> friend.party | arrived(home=False)
    ride -> at_home | arrived(home=True)
    party -> wait_car, friend.party -> friend.at_home | tired

    on_rest_started -> idle
    on_wanna_party -> search
    on_wait_guest -> idle
    on_wait_car -> want to cancel
    on_ride_started -> idle
    on_party_started -> idle
    """

    def __init__(
        self,
        name: str,
        home: "Point",
        balance: float,
        *,
        id: uuid.UUID | None = None,
        on_rest_started: Callable[[], None] | None = None,
        on_wanna_party: Callable[[], None] | None = None,
        on_friend_found: Callable[[], None] | None = None,
        on_ordering_car: Callable[[], None] | None = None,
        on_wait_car: Callable[[], None] | None = None,
        on_ride_started: Callable[[], None] | None = None,
        on_wait_guest: Callable[[], None] | None = None,
        on_party_started: Callable[[], None] | None = None,
    ) -> None:
        self.id: uuid.UUID = id or uuid.uuid4()
        self.name = name
        self.balance = balance
        self.pos = home
        self.home = home

        self._ride_src_dest: tuple["Point", "Point"] | None = None
        self._is_host: bool | None = None
        self._friend: "Human" | None = None
        self._ride: "Ride" | None = None

        self.on_rest_started = Callback.from_optional(on_rest_started)
        self.on_wanna_party = Callback.from_optional(on_wanna_party)
        self.on_friend_found = Callback.from_optional(on_friend_found)
        self.on_ordering_car = Callback.from_optional(on_ordering_car)
        self.on_wait_guest = Callback.from_optional(on_wait_guest)
        self.on_wait_car = Callback.from_optional(on_wait_car)
        self.on_ride_started = Callback.from_optional(on_ride_started)
        self.on_party_started = Callback.from_optional(on_party_started)
        self._smachine = self._build_fsm()

    @property
    def is_host(self) -> bool:
        return _ensureattr(self._is_host, "is_host")

    @property
    def friend(self) -> "Human":
        return _ensureattr(self._friend, "friend")

    @property
    def order_src_dest(self) -> tuple["Point", "Point"]:
        return _ensureattr(self._ride_src_dest, "_ride_src_dest")

    @property
    def ride(self) -> "Ride":
        return _ensureattr(self._ride, "ride")

    @property
    def is_in_ride(self) -> bool:
        return self._ride is not None

    @property
    def is_at_home(self) -> bool:
        return self.pos == self.home

    @property
    def is_resting(self) -> bool:
        return self.state == State.Rest

    @property
    def is_searching_friend(self) -> bool:
        return self.state == State.WannaParty

    def _order_car(self, source: "Point", dest: "Point") -> None:
        self._ride_src_dest = source, dest

    def _invited_by(self, friend: "Human") -> None:
        self._is_host = False
        self._friend = friend

    def _host_party(self, guest: "Human") -> None:
        self._is_host = True
        self._friend = guest

    def _assign_ride(self, ride: "Ride") -> None:
        self._ride = ride

    def _arrived_to_party(self) -> None:
        self.pos = self.friend.home
        self._ride = None

    def _reset_context(self) -> None:
        self.pos = self.home
        self._is_host = None
        self._friend = None
        self._ride = None

    def _build_fsm(self) -> transitions.Machine:
        machine = transitions.Machine(
            self,
            states=[
                transitions.State(
                    State.Rest, on_enter=[self.on_rest_started, self._reset_context]
                ),
                transitions.State(
                    State.WannaParty,
                    on_enter=self.on_wanna_party,
                    on_exit=self.on_friend_found,
                ),
                transitions.State(State.WaitGuest, on_enter=self.on_wait_guest),
                transitions.State(State.OrderingCar, on_enter=self.on_ordering_car),
                transitions.State(State.AwaitingRide, on_enter=self.on_wait_car),
                transitions.State(State.Ride, on_enter=self.on_ride_started),
                transitions.State(State.Party, on_enter=self.on_party_started),
            ],
            initial=State.Rest,
            transitions=[
                {
                    "trigger": "feel_lonely",
                    "source": State.Rest,
                    "dest": State.WannaParty,
                },
            ],
        )

        # Guest branch
        machine.add_transitions(
            [
                {
                    "trigger": "invited_by",
                    "source": State.WannaParty,
                    "dest": State.OrderingCar,
                    "before": [
                        self._invited_by,
                        lambda f: self._order_car(self.home, f.home),
                    ],
                },
                {
                    "trigger": "cancel_party",
                    "source": State.OrderingCar,
                    "dest": State.Rest,
                },
                {
                    "trigger": "ordered_ride",
                    "source": State.OrderingCar,
                    "dest": State.AwaitingRide,
                    "before": self._assign_ride,
                },
                {
                    "trigger": "car_arrived",
                    "source": State.AwaitingRide,
                    "dest": State.Ride,
                },
                {
                    "trigger": "skip_ride",
                    "source": State.AwaitingRide,
                    "dest": State.Party,
                    "conditions": "is_at_home",
                    "after": self._arrived_to_party,
                },
                {
                    "trigger": "skip_ride",
                    "source": [State.AwaitingRide, State.OrderingCar],
                    "dest": State.Rest,
                    "unless": "is_at_home",
                },
                {
                    "trigger": "arrived",
                    "source": State.Ride,
                    "dest": State.Party,
                    "conditions": "is_at_home",
                    "after": self._arrived_to_party,
                },
                {
                    "trigger": "arrived",
                    "source": State.Ride,
                    "dest": State.Rest,
                    "unless": "is_at_home",
                },
                {
                    "trigger": "tired",
                    "source": State.Party,
                    "dest": State.OrderingCar,
                    "unless": "is_host",
                    "before": lambda: self._order_car(self.pos, self.home),
                },
            ]
        )

        # Organizer branch
        machine.add_transitions(
            [
                {
                    "trigger": "host_party",
                    "source": State.WannaParty,
                    "dest": State.WaitGuest,
                    "before": self._host_party,
                },
                {
                    "trigger": "cancel_party",
                    "source": State.WaitGuest,
                    "dest": State.Rest,
                },
                {
                    "trigger": "guest_arrived",
                    "source": State.WaitGuest,
                    "dest": State.Party,
                },
                {
                    "trigger": "tired",
                    "source": State.Party,
                    "dest": State.Rest,
                    "conditions": "is_host",
                },
            ]
        )

        return machine
