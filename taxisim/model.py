from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

import faker
import mesa
import tqdm
from mesa.datacollection import DataCollector
from mesa.time import BaseScheduler

from taxisim import ticks
from taxisim.agents import CarAgent
from taxisim.agents import HumanAgent
from taxisim.agents.strat import CarWaiter
from taxisim.agents.strat import random_checker
from taxisim.agents.strat import wait_n_ticks
from taxisim.friends import FriendsService
from taxisim.human import Human
from taxisim.point import Point
from taxisim.taxi.car import Car
from taxisim.taxi.metrics import inject_metrics
from taxisim.taxi.taxi import TaxiService

if TYPE_CHECKING:
    from pandas import DataFrame

FAKE = faker.Faker()


def _default_city_box() -> tuple[Point, Point]:
    return Point.from_numbers(0, 0), Point.from_numbers(100, 100)


@dataclass(frozen=True)
class Parameters:
    lonely_chance: float = 0.001
    tired_chance: float = 0.001
    car_speed: int = 10
    city_box: tuple[Point, Point] = field(default_factory=_default_city_box)
    initial_balance: float = 100.0
    balance_increment: float = 5.0
    waiter: CarWaiter | None = None
    wait_time: int = 60


class SimulationModel(mesa.Model):
    def __init__(
        self,
        cars: int,
        people: int,
        n_ticks: int,
        taxi: TaxiService,
        friends: FriendsService,
        parameters: Parameters | None = None,
    ) -> None:
        super().__init__()

        self.n_ticks = n_ticks
        self.taxi = taxi
        self.metrics = inject_metrics(self.taxi)
        self.friends = friends
        self.people: list[Human] = []
        self.cars: list[Car] = []
        self.parameters = parameters or Parameters()
        self.datacollector = DataCollector(
            model_reporters={
                "AverageWaitTime": lambda model: model.metrics.avg_wait_time,
                "RidesCancelled": lambda model: model.metrics.cancelled,
                "RidesFinished": lambda model: model.metrics.finished,
                "RidesSoFar": lambda model: model.metrics.total,
                "MoneyEarned": lambda model: model.metrics.money_earned,
                "MoneyLost": lambda model: model.metrics.money_lost,
                # "DistancePassed": lambda model: model.metrics.latest.distance,
            }
        )

        self.scheduler = BaseScheduler(self)
        waiter = self.parameters.waiter or wait_n_ticks(self.parameters.wait_time)
        for _ in range(people):
            human = Human(
                name=FAKE.name(),
                home=Point.any_within(*self.parameters.city_box),
                balance=self.parameters.initial_balance,
            )
            agent = HumanAgent(
                self,
                human,
                should_wait=waiter,
                lonely_checker=random_checker(self.parameters.lonely_chance),
                tired_checker=random_checker(self.parameters.tired_chance),
                taxi_api=self.taxi,
                friends_api=self.friends,
            )
            self.people.append(human)
            self.scheduler.add(agent)

        for _ in range(cars):
            car = Car(
                pos=Point.any_within(*self.parameters.city_box),
                speed=self.parameters.car_speed,
            )
            agent = CarAgent(self, car)
            self.taxi.register_car(car)
            self.cars.append(car)
            self.scheduler.add(agent)

    def get_statistics(self) -> "DataFrame":
        return self.datacollector.get_model_vars_dataframe()

    def step(self) -> None:
        self.datacollector.collect(self)
        self.scheduler.step()
        ticks.increment()
        for human in self.people:
            human.balance += self.parameters.balance_increment

    def run_model(self, with_progress: bool = False) -> None:
        ticks.reset()
        if with_progress:
            rng = tqdm.trange(self.n_ticks)
        else:
            rng = range(self.n_ticks)

        for _ in rng:
            self.step()

        self.n_ticks = 0
        self.running = False
