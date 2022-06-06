from typing import Callable

from taxisim.human import Human
from taxisim.point import Point
from taxisim.taxi.car import Car
from taxisim.taxi.ride import Ride
from taxisim.taxi.taxi import TaxiServiceAPI


def _add_average(avg1: float, size1: int, avg2: float, size2: int = 1) -> float:
    return (size1 * avg1 + size2 * avg2) / (size1 + size2)


class MetricsRecord:
    def __init__(
        self,
        finished: list[Ride] | None = None,
        cancelled: list[Ride] | None = None,
        distance: float = 0.0,
        money_earned: float = 0.0,
        money_lost: float = 0.0,
        avg_wait_time: float = 0.0,
    ) -> None:
        self.finished: list[Ride] = finished or []
        self.cancelled: list[Ride] = cancelled or []
        self.distance = distance
        self.money_earned = money_earned
        self.money_lost = money_lost
        self.avg_wait_time = avg_wait_time

    def add_ride(self, ride: Ride, price: float):
        self.distance += ride.source.distance_to(ride.dest)
        self.avg_wait_time = _add_average(
            self.avg_wait_time, self.rides, ride.wait_time
        )

        if not ride.is_cancelled:
            self.money_earned += price
            self.finished.append(ride)
        else:
            self.money_lost += price
            self.cancelled.append(ride)

    def merge(self, other: "MetricsRecord", inplace: bool = False) -> "MetricsRecord":
        record = self if inplace else MetricsRecord()
        record.finished = self.finished + other.finished
        record.cancelled = self.cancelled + other.cancelled
        record.distance = self.distance + other.distance
        record.money_earned = self.money_earned + other.money_earned
        record.money_earned = self.money_lost + other.money_lost
        record.avg_wait_time = _add_average(
            self.avg_wait_time, self.rides, other.avg_wait_time, other.rides
        )

        return record

    @property
    def rides_cancelled(self) -> int:
        return len(self.cancelled)

    @property
    def rides_finished(self) -> int:
        return len(self.finished)

    @property
    def rides(self) -> int:
        return self.rides_cancelled + self.rides_finished


class TaxiMetrics:
    def __init__(self, records: list[MetricsRecord] | None = None) -> None:
        self.records = records or [MetricsRecord()]

    def new_record(self) -> None:
        self.records.append(MetricsRecord())

    def add_ride(self, ride: Ride, price: float) -> None:
        self.latest.add_ride(ride, price)

    def get_total(self) -> MetricsRecord:
        total = MetricsRecord()
        for record in self.records:
            total.merge(record, inplace=True)

        return total

    @property
    def latest(self) -> MetricsRecord:
        return self.records[-1]


def inject_metrics(service: TaxiServiceAPI) -> TaxiMetrics:
    metrics = TaxiMetrics()

    def add_ride(ride: Ride) -> None:
        price = service.get_price(ride.source, ride.dest)
        metrics.add_ride(ride, price)

    def request_ride(
        source: "Point",
        dest: "Point",
        passenger: "Human",
        on_car_assigned: Callable[["Car"], None],
        on_car_arrived: Callable[[], None],
    ) -> Ride:
        ride = service.request_ride(
            source,
            dest,
            passenger=passenger,
            on_car_arrived=on_car_arrived,
            on_car_assigned=on_car_assigned,
        )
        ride.on_ride_cancelled.subscribe(lambda: add_ride(ride))
        ride.on_ride_finished.subscribe(lambda: add_ride(ride))

        return ride

    setattr(service, "request_ride", request_ride)
    return metrics
