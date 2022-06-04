import time
import uuid
from dataclasses import dataclass
from dataclasses import field
from queue import PriorityQueue
from typing import TYPE_CHECKING
from typing import Callable

from taxisim.service import EventServer
from taxisim.taxi.ride import Ride

if TYPE_CHECKING:
    from taxisim.human import Human
    from taxisim.point import Point
    from taxisim.taxi.car import Car
    from taxisim.taxi.finder import CarFinder


@dataclass(order=True)
class RideEvent:
    priority: float
    ride: Ride = field(compare=False)

    @classmethod
    def timebased(cls, ride: Ride):
        return cls(-time.time(), ride)


class TaxiService:
    def __init__(self, car_finder: "CarFinder", *, daemon: bool = True) -> None:
        self.car_finder = car_finder

        self._rides: dict[uuid.UUID, Ride] = {}
        self._free_cars: dict[uuid.UUID, "Car"] = {}
        self._events: EventServer[RideEvent] = EventServer(
            self._handle_ride, daemon=daemon, queue=PriorityQueue()
        )

    def _handle_ride(self, event: RideEvent) -> bool:
        car = self.car_finder(event.ride, self._rides.values())
        if car is not None:
            event.ride.assign_car(car)
            return True

        return False

    def add_car(self, car: "Car") -> None:
        if car.id in self._free_cars:
            raise RuntimeError("Car already registered")

        self._free_cars[car.id] = car

    def _add_ride_car(self, ride_id: uuid.UUID) -> None:
        ride = self.get_ride_info(ride_id)
        if ride.car is not None:
            self.add_car(ride.car)

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
    ) -> uuid.UUID:
        ride_id = uuid.uuid4()
        ride = Ride(
            source,
            dest,
            passenger=passenger,
            id=ride_id,
            on_car_assigned=on_car_assigned,
            on_car_arrived=on_car_arrived,
            on_ride_cancelled=lambda: self._add_ride_car(ride_id),
            on_ride_finished=lambda: self._add_ride_car(ride_id),
        )
        self._events.emit(RideEvent.timebased(ride))
        return ride.id

    def cancel_ride(self, id: uuid.UUID) -> None:
        ride = self.get_ride_info(id)
        ride.cancel()
