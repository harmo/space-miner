""" Ore: held by the asteroids, extracted by the laser of the ship, and
carried in its cargo """

import math
from dataclasses import dataclass

from ..colors import Rgb
from ..world.space import Celestial
from .config import ORE_DENSITY
from .minerals import MINERALS, Mineral

Hold = dict[str, float]       # units of ore, by mineral

# Less ore than this is what rounding left, not ore
EPSILON = 1e-6


def ore_in(radius: float) -> float:
    return ORE_DENSITY * radius ** 2


def mineral_of(asteroid: Celestial) -> Mineral:
    return MINERALS[asteroid.mineral or 'rock']


def whole_units(amount: float) -> int:
    """ Rounded down, but sums of floats like 19.999999 count as 20 """
    return int(amount + EPSILON)


def withdraw(hold: Hold, name: str, units: float) -> None:
    """ Emptied, it no longer holds `name` """
    left = hold.get(name, 0.) - units
    if left > EPSILON:
        hold[name] = left
    else:
        hold.pop(name, None)


def cargo_total(ore: Hold) -> int:
    """ Units of ore of every mineral """
    return sum(whole_units(amount) for amount in ore.values())


def cargo_load(ore: Hold) -> float:
    return sum(ore.values())


def cargo_room(ore: Hold, capacity: float) -> float:
    """ Ore that still fits in the cargo """
    room = capacity - cargo_load(ore)
    return room if room > EPSILON else 0.


def cargo_fill(ore: Hold, capacity: float) -> float:
    """ From 0 when empty to 1 when full """
    return min(1., cargo_load(ore) / capacity)


@dataclass(frozen=True)
class CargoLine:
    """ What the cargo shows for one mineral """
    mineral: str
    name: str
    amount: int
    color: Rgb
    mining: bool              # being extracted right now


def cargo_lines(ore: Hold,
                mining: str | None) -> list[CargoLine]:
    """ Minerals in the cargo, and the one being mined even before the
    first unit, in the order of the minerals table """
    lines = [
        CargoLine(
            name, mineral.name, whole_units(ore.get(name, 0.)),
            mineral.color, name == mining,
        )
        for name, mineral in MINERALS.items()
    ]
    return [line for line in lines if line.amount > 0 or line.mining]


class Deposits:
    """ Ore left in each asteroid, which is full until mined """

    def __init__(self) -> None:
        self._left: dict[int, float] = {}

    def left(self, asteroid: Celestial) -> float:
        return self._left.get(asteroid.entity_id, ore_in(asteroid.radius))

    def progress(self, asteroid: Celestial) -> float:
        """ From 0 when untouched to 1 when mined out """
        return 1. - self.left(asteroid) / ore_in(asteroid.radius)

    def mine(self, asteroid: Celestial, dt: float, rate: float,
             room: float = math.inf) -> float:
        """ Extract ore at `rate` for dt seconds, no more than `room`,
        returns how much """
        left = self.left(asteroid)
        extracted = min(left, rate * dt, room)
        self._left[asteroid.entity_id] = left - extracted
        return extracted

    def forget(self, asteroid: Celestial) -> None:
        """ Entity ids get reused once the asteroid is gone """
        self._left.pop(asteroid.entity_id, None)
