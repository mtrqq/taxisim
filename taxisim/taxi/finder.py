from typing import Callable, Container, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ride import Ride
    from .car import Car


CarFinder = Callable[[Ride, Container[Car]], Optional[Car]]
