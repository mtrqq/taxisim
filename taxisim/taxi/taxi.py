import time
import uuid
from dataclasses import dataclass
from dataclasses import field
from queue import PriorityQueue
from typing import TYPE_CHECKING, Iterable, List, Protocol
from typing import Callable

from pyparsing import Optional

from taxisim.service import EventServer
from taxisim.taxi.ride import Ride

if TYPE_CHECKING:
    from taxisim.human import Human
    from taxisim.point import Point
    from taxisim.taxi.car import Car
    from taxisim.taxi.strat import CarFinder
    from taxisim.taxi.strat import PriceCalculator


@dataclass(order=True)
class RideEvent:
    priority: float
    ride: Ride = field(compare=False)

    @classmethod
    def timebased(cls, ride: Ride):
        return cls(-time.time(), ride)


class TaxiServiceAPI(Protocol):
    def register_car(self, car: "Car") -> None:
        ...

    def register_cars(self, cars: Iterable["Car"]) -> None:
        ...

    def get_ride_info(self, id: uuid.UUID) -> Ride:
        ...

    def get_price(self, source: "Point", dest: "Point") -> float:
        ...

    def request_ride(
        self,
        source: "Point",
        dest: "Point",
        passenger: "Human",
        on_car_assigned: Callable[["Car"], None],
        on_car_arrived: Callable[[], None],
    ) -> Ride:
        ...

    def cancel_ride(self, id: uuid.UUID) -> None:
        ...


# TODO: thread safety for car state
class TaxiService:
    def __init__(
        self,
        car_finder: "CarFinder",
        price_calculator: PriceCalculator,
        *,
        daemon: bool = True,
    ) -> None:
        self.car_finder = car_finder
        self.price_calculator = price_calculator

        self._rides: dict[uuid.UUID, Ride] = {}
        self._reg_cars: dict[uuid.UUID, "Car"] = {}
        self._free_cars: dict[uuid.UUID, "Car"] = {}
        self._events: EventServer[RideEvent] = EventServer(
            self._handle_ride, daemon=daemon, queue=PriorityQueue()
        )

    def _handle_ride(self, event: RideEvent) -> bool:
        car = self.car_finder(event.ride, self._free_cars.values())
        if car is not None:
            event.ride.assign_car(car)
            return True

        return False

    def register_car(self, car: "Car") -> None:
        if car.id in self._free_cars:
            raise RuntimeError("Car already registered")

        self._free_cars[car.id] = car

    def register_cars(self, cars: Iterable["Car"]) -> None:
        for car in cars:
            self.register_car(car)

    # def _add_ride_car(self, ride_id: uuid.UUID) -> None:
    #     ride = self.get_ride_info(ride_id)
    #     if ride.car is not None:
    #         self.register_car(ride.car)

    def get_ride_info(self, id: uuid.UUID) -> Ride:
        try:
            return self._rides[id]
        except KeyError:
            raise RuntimeError(f"Ride with id {id} not found") from None

    def request_ride(
        self,
        source: "Point",
        dest: "Point",
        passenger: "Human",
        on_car_assigned: Callable[["Car"], None],
        on_car_arrived: Callable[[], None],
    ) -> Ride:
        ride_id = uuid.uuid4()
        ride = Ride(
            source,
            dest,
            passenger=passenger,
            id=ride_id,
            on_car_assigned=on_car_assigned,
            on_car_arrived=on_car_arrived,
        )
        self._events.emit(RideEvent.timebased(ride))
        return ride

    def get_price(self, source: "Point", dest: "Point") -> float:
        return self.price_calculator(source, dest)

    def cancel_ride(self, id: uuid.UUID) -> None:
        ride = self.get_ride_info(id)
        ride.cancel()
