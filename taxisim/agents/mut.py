from typing import Callable

import mesa


class MutableBehaviourAgent(mesa.Agent):
    def __init__(
        self,
        unique_id,
        model,
        behaviour=None,
    ):
        self.behaviour = behaviour or self.idle
        super().__init__(unique_id, model)

    def change_behaviour(self, behaviour):
        self.behaviour = behaviour

    def changer(self, behaviour):
        """Creates a callback to defer behaviour changing"""
        return lambda *_: self.change_behaviour(behaviour)

    def idle(self):
        pass

    def step(self):
        return self.behaviour()
