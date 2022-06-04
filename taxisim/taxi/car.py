import enum
from typing import TYPE_CHECKING, Optional
import uuid

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
        id: Optional[uuid.UUID] = None,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.speed = speed
        self.pos = pos