import enum
from typing import Callable
import uuid
import transitions
from taxisim.callback import Callback

from taxisim.point import Point
from taxisim.taxi.ride import Ride

class State:
    Rest: enum.Enum
    WannaParty: enum.Enum
    WaitGuest: enum.Enum
    AwaitingRide: enum.Enum
    Ride: enum.Enum
    Party: enum.Enum

class Human:
    id: uuid.UUID
    state: State
    name: str
    balance: float
    pos: Point
    home: Point

    on_rest_started: Callback[[]]
    on_wanna_party: Callback[[]]
    on_wait_guest: Callback[[]]
    on_wait_car: Callback[[]]
    on_ride_started: Callback[[]]
    on_party_started: Callback[[]]
    smachine: transitions.Machine

    def __init__(
        self,
        name: str,
        pos: "Point",
        home: "Point",
        balance: float,
        *,
        id: uuid.UUID | None = None,
        on_rest_started: Callable[[], None] | None = ...,
        on_wanna_party: Callable[[], None] | None = ...,
        on_wait_guest: Callable[[], None] | None = ...,
        on_wait_car: Callable[[], None] | None = ...,
        on_ride_started: Callable[[], None] | None = ...,
        on_party_started: Callable[[], None] | None = ...,
    ) -> None: ...
    @property
    def is_host(self) -> bool: ...
    @property
    def is_at_home(self) -> bool: ...
    @property
    def friend(self) -> Human: ...
    @property
    def ride(self) -> Ride: ...
    @property
    def is_in_ride(self) -> bool: ...
    def feel_lonely(self) -> None: ...
    def host_party(self, guest: Human) -> None: ...
    def invited_by(self, friend: Human) -> None: ...
    def ordered_ride(self, ride: Ride) -> None: ...
    def car_arrived(self) -> None: ...
    def guest_arrived(self) -> None: ...
    def arrived(self) -> None: ...
    def tired(self) -> None: ...
