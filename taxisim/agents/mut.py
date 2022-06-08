from typing import Callable

import mesa


class MutableBehaviourAgent(mesa.Agent):
    def __init__(
        self,
        unique_id: int,
        model: mesa.Model,
        behaviour: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(unique_id, model)
        self.behaviour = behaviour or self.idle

    def change_behaviour(self, behaviour: Callable[[], None]) -> None:
        self.behaviour = behaviour

    def changer(self, behaviour: Callable[[], None]) -> Callable[..., None]:
        """Creates a callback to defer behaviour changing"""
        return lambda *_: self.change_behaviour(behaviour)

    def idle(self) -> None:
        pass

    def step(self) -> None:
        return self.behaviour()
