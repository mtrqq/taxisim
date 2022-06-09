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
    OrderingCar: enum.Enum
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
    on_friend_found: Callback[[]]
    on_ordering_car: Callback[[]]
    on_wait_guest: Callback[[]]
    on_wait_car: Callback[[]]
    on_ride_started: Callback[[]]
    on_party_started: Callback[[]]

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
    ) -> None: ...
    @property
    def is_searching_friend(self) -> bool: ...
    @property
    def is_host(self) -> bool: ...
    @property
    def is_at_home(self) -> bool: ...
    @property
    def friend(self) -> Human: ...
    @property
    def order_src_dest(self) -> tuple["Point", "Point"]: ...
    @property
    def ride(self) -> Ride: ...
    @property
    def is_resting(self) -> bool: ...
    @property
    def is_in_ride(self) -> bool: ...
    def feel_lonely(self) -> None: ...
    def host_party(self, guest: Human) -> None: ...
    def cancel_party(self) -> None: ...
    def invited_by(self, friend: Human) -> None: ...
    def ordered_ride(self, ride: Ride) -> None: ...
    def skip_ride(self) -> None: ...
    def car_arrived(self) -> None: ...
    def guest_arrived(self) -> None: ...
    def arrived(self) -> None: ...
    def tired(self) -> None: ...
