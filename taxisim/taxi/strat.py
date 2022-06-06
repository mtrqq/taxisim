from typing import TYPE_CHECKING
from typing import Callable
from typing import Container
from typing import Optional

if TYPE_CHECKING:
    from taxisim.taxi.car import Car
    from taxisim.taxi.ride import Ride
    from taxisim.point import Point


CarFinder = Callable[["Ride", Container["Car"]], Optional["Car"]]
PriceCalculator = Callable[["Point", "Point"], float]