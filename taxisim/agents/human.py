from typing import Callable
from typing import ParamSpec
from typing import TypeVar

import mesa

from taxisim.agents.mut import MutableBehaviourAgent
from taxisim.agents.strat import CarWaiter
from taxisim.agents.strat import StatusChecker
from taxisim.callback import Callback
from taxisim.friends import FriendsService
from taxisim.friends import Role
from taxisim.human import Human
from taxisim.taxi import TaxiService

P = ParamSpec("P")
T = TypeVar("T")


def _once(fun):
    called = False

    def wrapper(*args, **kwargs):
        nonlocal called

        if not called:
            fun(*args, **kwargs)
        called = True

    return wrapper


class HumanAgent(MutableBehaviourAgent):
    def __init__(
        self,
        model,
        human,
        should_wait,
        lonely_checker,
        tired_checker,
        taxi_api,
        friends_api,
    ):
        if not human.is_resting:
            raise ValueError("Human should be in 'initial' state")

        super().__init__(human.id.int, model, self._check_is_lonely)
        human.on_rest_started.subscribe(self.changer(self._check_is_lonely))
        human.on_wanna_party.subscribe(
            lambda *_: self._search_friend(), self.changer(self.idle)
        )
        human.on_wait_guest.subscribe(self.changer(self.idle))
        human.on_ordering_car.subscribe(lambda *_: self._order_car())
        human.on_wait_car.subscribe(self.changer(self._wait_car))
        human.on_ride_started.subscribe(self.changer(self.idle))
        human.on_party_started.subscribe(
            Callback[[]](
                self._notify_host,
                self.changer(self._check_tired),
            )
        )

        self.human = human
        self.taxi_api = taxi_api
        self.friends_api = friends_api
        self.should_wait = should_wait
        self.lonely_checker = lonely_checker
        self.tired_checker = tired_checker

    def _check_is_lonely(self):
        if self.lonely_checker():
            self.human.feel_lonely()

    def _notify_host(self):
        if not self.human.is_host:
            self.human.friend.guest_arrived()

    def _search_friend(self):
        self.friends_api.find_friend(
            me=self.human,
            on_found=self._friend_found,
        )

    def _friend_found(self, friend, role):
        if role == Role.Host:
            self.behaviour = _once(lambda: self.human.host_party(friend))
        elif role == Role.Guest:
            self.behaviour = _once(lambda: self.human.invited_by(friend))
        else:
            raise RuntimeError(f"Unresolved role {role} encountered")

    def _check_tired(self):
        if self.tired_checker():
            self.human.friend.tired()
            self.human.tired()

    def _order_car(self):
        source, dest = self.human.order_src_dest
        ride_price = self.taxi_api.get_price(source, dest)

        if self.human.balance < ride_price:
            if not self.human.is_at_home:
                self.human.skip_ride()
            else:
                self.human.cancel_party()
                self.human.friend.cancel_party()
        else:
            ride = self.taxi_api.request_ride(
                source=source,
                dest=dest,
                passenger=self.human,
                on_car_arrived=lambda: self.human.car_arrived(),
                on_ride_finished=lambda: self.human.arrived(),
            )

            self.human.balance - ride_price
            self.human.ordered_ride(ride)

    def _wait_car(self):
        if self.human.car_is_waiting:
            self.human.sit_into_car()

        ride = self.human.ride
        if not self.should_wait(
            ride.wait_time,
            self.taxi_api.get_price(ride.source, ride.dest),
        ):
            self.taxi_api.cancel_ride(ride.id)
            self.human.skip_ride()
