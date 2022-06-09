import math
import random
from dataclasses import dataclass
from typing import Any
from typing import ClassVar
from typing import Container
from typing import Iterator

import numpy as np
from numpy.typing import NDArray

Number = int | float


def _order(x, y):
    if x < y:
        return x, y
    else:
        return y, x


@dataclass
class Point:
    PRECISION = 0.001

    array: NDArray

    @classmethod
    def from_array(cls, container):
        return cls(array=np.array(container))

    @classmethod
    def from_numbers(cls, *numbers):
        return cls(array=np.array(numbers))

    @classmethod
    def any_within(cls, p1, p2):
        if p1.dims != p2.dims:
            raise ValueError(
                f"Incompatible dimmensions for points ({p1.dims}, {p2.dims})"
            )

        coords = [random.uniform(*_order(c1, c2)) for c1, c2 in zip(p1, p2)]
        return cls.from_array(coords)

    def vector_to(self, other):
        return Point(self.array - other.array)

    def distance_to(self, other):
        return math.hypot(*self.vector_to(other))

    def advanced(self, to, by):
        distance = self.distance_to(to)
        if distance == 0.0:
            return self

        ratio = by / distance
        nratio = 1 - ratio

        return Point.from_array(
            [nratio * src + ratio * dest for src, dest in zip(self, to)]
        )

    @property
    def dims(self):
        return len(self.array)

    def __getitem__(self, index):
        return self.array[index]

    def __iter__(self):
        return iter(self.array)

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented

        return np.isclose(self.array, other.array, atol=self.PRECISION).all()

    def __repr__(self):
        return f"Point({str(self.array)})"
