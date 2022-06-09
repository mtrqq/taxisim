from typing import TYPE_CHECKING
from typing import Callable
from typing import Collection
from typing import Optional

if TYPE_CHECKING:
    from taxisim.point import Point
    from taxisim.taxi.car import Car
    from taxisim.taxi.ride import Ride


CarFinder = Callable[["Ride", Collection["Car"]], Optional["Car"]]
PriceCalculator = Callable[["Point", "Point"], float]


def price_per_unit(price):
    def calculator(p1, p2):
        return p1.distance_to(p2) * price

    return calculator


def any_free_car():
    def finder(_, cars):
        for car in cars:
            if car.is_free:
                return car

        return None

    return finder


def closest_free_car():
    def finder(ride, cars):
        cars = sorted(cars, key=lambda car: ride.source.distance_to(car.pos))
        for car in cars:
            if car.is_free:
                return car

        return None

    return finder
