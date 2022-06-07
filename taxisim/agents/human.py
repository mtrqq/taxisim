import random

import mesa

from taxisim.agents.mut import MutableBehaviourAgent
from taxisim.agents.wait import CarWaiter
from taxisim.callback import Callback
from taxisim.friends import FriendsService
from taxisim.friends import Role
from taxisim.human import Human
from taxisim.taxi import TaxiService

LONELY_CHANCE: float = 0.001
TIRED_CHANCE: float = 0.001


def _check_chance(chance: float) -> bool:
    return random.random() <= chance


class HumanAgent(MutableBehaviourAgent):
    def __init__(
        self,
        model: mesa.Model,
        human: Human,
        should_wait: CarWaiter,
        taxi_api: TaxiService,
        friends_api: FriendsService,
    ) -> None:
        if not human.is_resting:
            raise ValueError("Human should be in 'initial' state")

        super().__init__(human.id.int, model, self._check_is_lonely)
        human.on_rest_started.subscribe(self.changer(self._check_is_lonely))
        human.on_wanna_party.subscribe(self.changer(self._search_friend))
        human.on_wait_guest.subscribe(self.changer(self.idle))
        human.on_ordering_car.subscribe(self.changer(self._wait_car))
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

    def _check_is_lonely(self) -> None:
        if _check_chance(LONELY_CHANCE):
            self.human.feel_lonely()

    def _notify_host(self) -> None:
        if not self.human.is_host:
            self.human.friend.guest_arrived()

    def _search_friend(self) -> None:
        self.friends_api.find_friend(
            me=self.human,
            on_found=self._friend_found,
        )

    def _friend_found(self, friend: Human, role: Role) -> None:
        if role == Role.Host:
            self.human.host_party(friend)
        elif role == Role.Guest:
            self.human.invited_by(friend)
        else:
            raise RuntimeError(f"Unresolved role {role} encountered")

    def _check_tired(self) -> None:
        if _check_chance(TIRED_CHANCE):
            self.human.tired()
            self.human.friend.tired()

    def _order_car(self) -> None:
        source, dest = self.human.order_src_dest
        ride = self.taxi_api.request_ride(
            source=source,
            dest=dest,
            passenger=self.human,
            on_car_arrived=lambda: self.human.car_arrived(),
        )

        self.human.ordered_ride(ride)

    def _wait_car(self) -> None:
        ride = self.human.ride

        if not self.should_wait(
            ride.wait_time,
            self.taxi_api.get_price(ride.source, ride.dest),
        ):
            self.taxi_api.cancel_ride(ride.id)
            self.human.skip_ride()
