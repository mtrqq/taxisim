import enum
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..point import Point


class State(enum.Enum):
    Free = 1
    Ride = 2


class Car:
    def __init__(
        self,
        speed: float,
        pos: Point,
        id: uuid.UUID | None = None,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.speed = speed
        self.pos = pos
