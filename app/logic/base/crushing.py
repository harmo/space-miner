""" The refinery of the base: the rock of the depot crushed a bit at a
time, each unit giving now and then a unit of some other ore, regolith
otherwise, back into the depot. It goes on while the ship is away. """

from dataclasses import dataclass
from random import Random

from ..mining.ore import Hold, whole_units, withdraw
from .config import CRUSH_RATE, CRUSH_YIELDS
from .unloading import depot_room


@dataclass(frozen=True)
class Refinery:
    """ How a post crushes its rock """
    rate: float = CRUSH_RATE  # units of rock a second
    yields: tuple[tuple[str, float], ...] = CRUSH_YIELDS  # found in a unit
    told: str = "la roche rend du fer, du cuivre, un peu d'or"


PLAIN_REFINERY = Refinery()


def sift(rng: Random, yields: tuple[tuple[str, float], ...]) -> str:
    """ What a unit of rock gives, regolith but for `yields` """
    draw = rng.random()
    for mineral, chance in yields:
        if draw < chance:
            return mineral
        draw -= chance
    return 'regolith'


class Crusher:

    def __init__(self, rng: Random,
                 refinery: Refinery = PLAIN_REFINERY) -> None:
        self.rng = rng
        self.refinery = refinery
        self.crushing = False
        self.ground = 0.          # rock crushed, not sifted yet

    def start(self, stock: Hold) -> None:
        self.crushing = whole_units(stock.get('rock', 0.)) > 0

    def update(self, stock: Hold, dt: float) -> list[str]:
        """ Returns what was found """
        if not self.crushing:
            return []
        crushed = min(stock.get('rock', 0.), self.refinery.rate * dt)
        withdraw(stock, 'rock', crushed)
        if 'rock' not in stock:
            self.crushing = False
        self.ground += crushed
        found = []
        while self.ground >= 1:
            self.ground -= 1
            mineral = sift(self.rng, self.refinery.yields)
            # Lost, with no room for it
            if depot_room(stock, mineral) >= 1:
                stock[mineral] = stock.get(mineral, 0.) + 1
            found.append(mineral)
        return found
