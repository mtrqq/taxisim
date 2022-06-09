from typing import Callable

from taxisim.human import Human
from taxisim.point import Point
from taxisim.taxi.car import Car
from taxisim.taxi.ride import Ride
from taxisim.taxi.taxi import TaxiService


def _add_average(avg1: float, size1: int, avg2: float, size2: int = 1) -> float:
    return (size1 * avg1 + size2 * avg2) / (size1 + size2)


class TaxiMetrics:
    def __init__(
        self,
        finished: int = 0,
        cancelled: int = 0,
        distance: float = 0.0,
        money_earned: float = 0.0,
        money_lost: float = 0.0,
        wait_times: list[float] | None = None,
    ) -> None:
        self.finished = finished
        self.cancelled = cancelled
        self.distance = distance
        self.money_earned = money_earned
        self.money_lost = money_lost
        self.wait_times = wait_times or []

    def add_ride(self, ride: Ride, price: float):
        self.distance += ride.source.distance_to(ride.dest)
        if ride.wait_time > 1000:
            ride.wait_time
        self.wait_times.append(ride.wait_time)

        if not ride.is_cancelled:
            self.money_earned += price
            self.finished += 1
        else:
            self.money_lost += price
            self.cancelled += 1

    @property
    def avg_wait_time(self) -> float:
        if len(self.wait_times) == 0:
            return 0.0

        return sum(self.wait_times) / len(self.wait_times)

    @property
    def total(self) -> int:
        return self.finished + self.cancelled


def inject_metrics(service: TaxiService) -> TaxiMetrics:
    metrics = TaxiMetrics()
    default_request_ride = service.request_ride

    def add_ride(ride: Ride) -> None:
        price = service.get_price(ride.source, ride.dest)
        metrics.add_ride(ride, price)

    def request_ride(
        source: "Point",
        dest: "Point",
        passenger: "Human",
        on_car_assigned: Callable[["Car"], None] | None = None,
        on_car_arrived: Callable[[], None] | None = None,
        on_ride_finished: Callable[[], None] | None = None,
    ) -> Ride:
        ride = default_request_ride(
            source,
            dest,
            passenger=passenger,
            on_car_arrived=on_car_arrived,
            on_car_assigned=on_car_assigned,
            on_ride_finished=on_ride_finished,
        )
        ride.on_ride_cancelled.subscribe(lambda: add_ride(ride))
        ride.on_ride_finished.subscribe(lambda: add_ride(ride))

        return ride

    setattr(service, "request_ride", request_ride)
    return metrics
