""" Fuel of the ship, in a single tank: burnt by thrusting, as much as the
thrusters push, and by the laser while it fires. Filled at posts. """

from typing import Literal

from .config import CRITICAL_FUEL, LOW_FUEL
from .lasers import laser
from .shipyard import ShipStats

FuelState = Literal['full', 'low', 'critical', 'empty']


def burn_rate(stats: ShipStats, thrust: float, firing: bool) -> float:
    """ Fuel a second, `thrust` from 0 to 1 """
    return stats.burn * thrust + (laser(stats.laser).burn if firing else 0.)


class Tank:

    def __init__(self, capacity: float) -> None:
        self.capacity = capacity
        self.level = capacity               # full

    @property
    def empty(self) -> bool:
        return self.level <= 0

    @property
    def share(self) -> float:
        """ From 0, empty, to 1, full """
        return self.level / self.capacity if self.capacity > 0 else 0.

    @property
    def missing(self) -> float:
        return self.capacity - self.level

    @property
    def state(self) -> FuelState:
        if self.empty:
            return 'empty'
        if self.share < CRITICAL_FUEL:
            return 'critical'
        return 'low' if self.share < LOW_FUEL else 'full'

    def burn(self, amount: float) -> None:
        self.level = max(0., self.level - amount)

    def fill(self, amount: float) -> None:
        self.level = min(self.capacity, self.level + amount)

    def resize(self, capacity: float) -> None:
        """ Another tank, refitting the ship: as much fuel as fits in it """
        self.capacity = capacity
        self.level = min(self.level, capacity)
