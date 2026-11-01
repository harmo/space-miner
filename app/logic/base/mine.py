""" The mine of an outpost, digging on its own into the depot, whether a
ship is there or not, for as long as the game runs and the depot has
room for what it digs """

from dataclasses import dataclass
from random import Random

from ..mining.ore import Hold
from .config import FRONTIER_YIELDS, MINE_RATE
from .unloading import depot_room

Yields = tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class Vein:
    """ What a mine digs """
    yields: Yields = FRONTIER_YIELDS        # how often each mineral comes up
    rate: float = MINE_RATE             # units a second, all of them


PLAIN_VEIN = Vein()


class Mine:

    def __init__(
        self,
        rng: Random,
        vein: Vein = PLAIN_VEIN
    ) -> None:
        self.rng = rng
        self.vein = vein
        self.dug = 0.             # units, not in the depot yet

    def update(self, stock: Hold, dt: float) -> None:
        if not self.diggable(stock):
            return
        self.dug += self.vein.rate * dt
        while self.dug >= 1:
            yields = self.diggable(stock)
            if not yields:
                return
            self.dug -= 1
            names = [name for name, _ in yields]
            weights = [share for _, share in yields]
            mineral = self.rng.choices(names, weights)[0]
            stock[mineral] = stock.get(mineral, 0.) + 1

    def diggable(self, stock: Hold) -> Yields:
        """ What the depot has room for """
        return tuple(
            (name, share) for name, share in self.vein.yields
            if depot_room(stock, name) >= 1
        )
