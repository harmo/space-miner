""" The refinery of the base: the rock of the depot crushed a bit at a
time, each unit giving now and then a unit of some other ore, regolith
otherwise, back into the depot. It goes on while the ship is away. """

from random import Random

from ..mining.ore import Hold, whole_units, withdraw
from .config import CRUSH_RATE, CRUSH_YIELDS


def sift(rng: Random) -> str:
    """ What a unit of rock gives """
    draw = rng.random()
    for mineral, chance in CRUSH_YIELDS:
        if draw < chance:
            return mineral
        draw -= chance
    return 'regolith'



class Crusher:

    def __init__(self, rng: Random) -> None:
        self.rng = rng
        self.crushing = False
        self.ground = 0.          # rock crushed, not sifted yet

    def start(self, stock: Hold) -> None:
        self.crushing = whole_units(stock.get('rock', 0.)) > 0

    def update(self, stock: Hold, dt: float) -> list[str]:
        """ Returns what was found """
        if not self.crushing:
            return []
        crushed = min(stock.get('rock', 0.), CRUSH_RATE * dt)
        withdraw(stock, 'rock', crushed)
        if 'rock' not in stock:
            self.crushing = False
        self.ground += crushed
        found = []
        while self.ground >= 1:
            self.ground -= 1
            mineral = sift(self.rng)
            stock[mineral] = stock.get(mineral, 0.) + 1
            found.append(mineral)
        return found
