import faker
import mesa
from mesa.time import BaseScheduler

from taxisim import ticks
from taxisim.agents import CarAgent
from taxisim.agents import HumanAgent
from taxisim.agents.strat import random_checker
from taxisim.agents.strat import wait_n_ticks
from taxisim.friends import FriendsService
from taxisim.human import Human
from taxisim.point import Point
from taxisim.taxi.car import Car
from taxisim.taxi.taxi import TaxiService

LONELY_CHANCE: float = 0.001
TIRED_CHANCE: float = 0.001
WAIT_TIME: int = 60
CAR_SPEED: int = 10
UNIT_PRICE: float = 0.0025
FAKE = faker.Faker()


class SimulationModel(mesa.Model):
    def __init__(
        self,
        cars: int,
        people: int,
        city_box: tuple[Point, Point],
        n_ticks: int,
        taxi: TaxiService,
        friends: FriendsService,
        init_balance: float = 100,
        balance_increment: float = 5,
        simulation_speed: int = 1,
    ) -> None:
        self.n_ticks = n_ticks
        self.city_box = city_box
        self.taxi = taxi
        self.friends = friends
        self.balance_increment = balance_increment
        self.simulation_speed = simulation_speed
        self.people: list[Human] = []
        self.cars: list[Car] = []

        self.scheduler = BaseScheduler(self)
        for _ in range(people):
            human = Human(
                name=FAKE.name(),
                home=Point.any_within(*city_box),
                balance=init_balance,
            )
            agent = HumanAgent(
                self,
                human,
                should_wait=wait_n_ticks(WAIT_TIME * simulation_speed),
                lonely_checker=random_checker(LONELY_CHANCE * simulation_speed),
                tired_checker=random_checker(TIRED_CHANCE * simulation_speed),
                taxi_api=self.taxi,
                friends_api=self.friends,
            )
            self.people.append(human)
            self.scheduler.add(agent)

        for _ in range(cars):
            car = Car(Point.any_within(*city_box), CAR_SPEED * simulation_speed)
            agent = CarAgent(self, car)
            self.cars.append(car)
            self.scheduler.add(agent)

    def step(self) -> None:
        self.scheduler.step()

        if ticks.increment_by(self.simulation_speed) > self.n_ticks:
            self.running = False

        for human in self.people:
            human.balance += self.balance_increment
