import time
import uuid
from dataclasses import dataclass
from dataclasses import field
from queue import PriorityQueue
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Iterable

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
    ride: Any = field(compare=False)

    @classmethod
    def timebased(cls, ride):
        return cls(-time.time(), ride)


class TaxiService:
    def __init__(
        self,
        car_finder,
        price_calculator,
        *,
        daemon=True,
    ):
        self.car_finder = car_finder
        self.price_calculator = price_calculator

        self._rides = {}
        self._free_cars = {}
        self._events = EventServer(
            self._handle_ride, daemon=daemon, queue=PriorityQueue()
        )

    def _handle_ride(self, event):
        if event.ride.is_cancelled:
            return True

        car = self.car_finder(event.ride, self._free_cars.values())
        if car is not None:
            if not event.ride.is_cancelled:
                car.accept_ride(event.ride)
                event.ride.assign_car(car)
            return True

        return False

    def _activate_car(self, car):
        self._free_cars[car.id] = car

    def _deactivate_car(self, car):
        del self._free_cars[car.id]

    def register_car(self, car):
        car.on_ride_accepted.subscribe(lambda *_: self._deactivate_car(car))
        car.on_ride_finished.subscribe(lambda: self._activate_car(car))

        if car.is_free:
            self._activate_car(car)

    def register_cars(self, cars):
        for car in cars:
            self.register_car(car)

    def get_ride_info(self, id):
        try:
            return self._rides[id]
        except KeyError:
            raise RuntimeError(f"Ride with id {id} not found") from None

    def request_ride(
        self,
        source,
        dest,
        passenger,
        on_car_assigned=None,
        on_car_arrived=None,
        on_ride_finished=None,
    ):
        ride_id = uuid.uuid4()
        ride = Ride(
            source,
            dest,
            passenger=passenger,
            id=ride_id,
            on_car_assigned=on_car_assigned,
            on_car_arrived=on_car_arrived,
            on_ride_finished=on_ride_finished,
        )
        self._events.emit(RideEvent.timebased(ride))
        self._rides[ride.id] = ride
        return ride

    def get_price(self, source, dest):
        return self.price_calculator(source, dest)

    def cancel_ride(self, id):
        ride = self.get_ride_info(id)
        if ride.car is not None:
            ride.car.cancel_ride()
        ride.cancel()

    def start(self):
        self._events.start()

    def shutdown(self, nowait=False):
        self._events.shutdown(nowait=nowait)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.shutdown()
