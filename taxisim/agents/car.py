from typing import cast

import mesa

from taxisim.agents.mut import MutableBehaviourAgent
from taxisim.point import Point
from taxisim.taxi.car import Car
from taxisim.taxi.ride import Ride


def _move_to(source: Point, dest: Point, distance_passed: float) -> Point:
    distance_between = source.distance_to(dest)
    if distance_passed > distance_between:
        return dest
    else:
        return source.advanced(dest, distance_passed)


class CarAgent(MutableBehaviourAgent):
    def __init__(self, model: mesa.Model, car: Car) -> None:
        if not car.is_free:
            raise ValueError("Human should be in 'initial' state")

        car.on_ride_accepted.subscribe(self.changer(self._move_to_src))
        car.on_passenger_picked_up.subscribe(self.changer(self._move_to_dest))
        car.on_ride_finished.subscribe(self.changer(self.idle))

        self.car = car
        super().__init__(self.car.id.int, model)

    def _move_to_src(self) -> None:
        ride = cast(Ride, self.car.ride)
        self.car.pos = _move_to(self.car.pos, ride.source, self.car.speed)

    def _move_to_dest(self) -> None:
        ride = cast(Ride, self.car.ride)
        self.car.pos = _move_to(self.car.pos, ride.dest, self.car.speed)
