import uuid
from typing import Sequence

import mesa

from taxisim.human import Human


class BalanceIncrementorAgent(mesa.Agent):
    def __init__(
        self, model: mesa.Model, people: Sequence[Human], increment: float
    ) -> None:
        super().__init__(uuid.uuid4().int, model)
        self.people = people
        self.increment = increment

    def step(self) -> None:
        for human in self.people:
            human.balance += self.increment
