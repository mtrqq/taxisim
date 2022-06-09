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


def _ensureattr(attr, name):
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
        name,
        home,
        balance,
        *,
        id=None,
        on_rest_started=None,
        on_wanna_party=None,
        on_friend_found=None,
        on_ordering_car=None,
        on_wait_car=None,
        on_ride_started=None,
        on_wait_guest=None,
        on_party_started=None,
    ):
        self.id = id or uuid.uuid4()
        self.name = name
        self.balance = balance
        self.pos = home
        self.home = home

        self._ride_src_dest = None
        self._is_host = None
        self._friend = None
        self._ride = None
        self._car_is_waiting = False

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
    def is_host(self):
        return _ensureattr(self._is_host, "is_host")

    @property
    def friend(self):
        return _ensureattr(self._friend, "friend")

    @property
    def order_src_dest(self):
        return _ensureattr(self._ride_src_dest, "_ride_src_dest")

    @property
    def ride(self):
        return _ensureattr(self._ride, "ride")

    @property
    def car_is_waiting(self):
        return self._car_is_waiting

    @property
    def is_in_ride(self):
        return self._ride is not None

    @property
    def is_at_home(self):
        return self.pos == self.home

    @property
    def is_resting(self):
        return self.state == State.Rest

    @property
    def is_searching_friend(self):
        return self.state == State.WannaParty

    def _order_car(self, source, dest):
        self._ride_src_dest = source, dest
        self._car_is_waiting = False

    def _invited_by(self, friend):
        self._is_host = False
        self._friend = friend

    def _host_party(self, guest):
        self._is_host = True
        self._friend = guest

    def _assign_ride(self, ride):
        self._ride = ride

    def _arrived_to_party(self):
        self.pos = self.friend.home
        self._ride = None

    def _reset_context(self):
        self.pos = self.home
        self._is_host = None
        self._friend = None
        self._ride = None
        self._car_is_waiting = False

    def _car_arrived(self):
        self._car_is_waiting = True

    def _try_sit_into_car(self):
        if self.car_is_waiting:
            self.ride.car.pick_up_passenger()
            self._car_is_waiting = None

    def _build_fsm(self):
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
                    "dest": State.AwaitingRide,
                    "after": self._car_arrived,
                },
                {
                    "trigger": "sit_into_car",
                    "source": State.AwaitingRide,
                    "dest": State.Ride,
                    "before": self._try_sit_into_car,
                    "after": self.on_ride_started,
                },
                {
                    "trigger": "skip_ride",
                    "source": [State.AwaitingRide, State.OrderingCar, State.Ride],
                    "dest": State.Party,
                    "conditions": "is_at_home",
                    "after": self._arrived_to_party,
                },
                {
                    "trigger": "skip_ride",
                    "source": [State.AwaitingRide, State.OrderingCar, State.Ride],
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

    def __repr__(self):
        return f"Human(name={self.name}, state={self.state.name})"
