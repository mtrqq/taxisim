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


def price_per_unit(price: float) -> PriceCalculator:
    def calculator(p1: "Point", p2: "Point") -> float:
        return p1.distance_to(p2) * price

    return calculator


def any_free_car() -> CarFinder:
    def finder(_: "Ride", cars: Collection["Car"]) -> Optional["Car"]:
        for car in cars:
            if car.is_free:
                return car

        return None

    return finder


def closest_free_car() -> CarFinder:
    def finder(ride: "Ride", cars: Collection["Car"]) -> Optional["Car"]:
        cars = sorted(cars, key=lambda car: ride.source.distance_to(car.pos))
        for car in cars:
            if car.is_free:
                return car

        return None

    return finder
