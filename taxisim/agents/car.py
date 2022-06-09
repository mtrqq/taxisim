from typing import cast

import mesa

from taxisim.agents.mut import MutableBehaviourAgent
from taxisim.point import Point
from taxisim.taxi.car import Car
from taxisim.taxi.ride import Ride


def _will_arrive_to(source: Point, dest: Point, speed: float) -> bool:
    return source.distance_to(dest) <= speed


class CarAgent(MutableBehaviourAgent):
    def __init__(self, model: mesa.Model, car: Car) -> None:
        if not car.is_free:
            raise ValueError("Human should be in 'initial' state")

        super().__init__(car.id.int, model)
        car.on_ride_accepted.subscribe(self.changer(self._move_to_src))
        car.on_waiting_passenger.subscribe(self.changer(self.idle))
        car.on_ride_started.subscribe(self.changer(self._move_to_dest))
        car.on_ride_finished.subscribe(self.changer(self.idle))
        self.car = car

    def _move_to_src(self) -> None:
        ride = cast(Ride, self.car.ride)
        if _will_arrive_to(self.car.pos, ride.source, self.car.speed):
            self.car.pos = ride.source
            self.car.arrive_to_source()
        else:
            self.car.pos = self.car.pos.advanced(ride.source, self.car.speed)

    def _move_to_dest(self) -> None:
        ride = cast(Ride, self.car.ride)
        if _will_arrive_to(self.car.pos, ride.dest, self.car.speed):
            self.car.pos = ride.dest
            self.car.arrive_to_dest()
        else:
            self.car.pos = self.car.pos.advanced(ride.dest, self.car.speed)
