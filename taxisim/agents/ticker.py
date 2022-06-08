import uuid

import mesa

from taxisim import ticks


class TicketAgent(mesa.Agent):
    def __init__(self, model: mesa.Model) -> None:
        super().__init__(uuid.uuid4().int, model)

    def step(self) -> None:
        ticks.increment()
