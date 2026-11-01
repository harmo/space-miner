""" The mine of an outpost, digging on its own into the depot, whether a
ship is there or not, for as long as the game runs and the depot has
room for what it digs """

from random import Random

from ..mining.ore import Hold
from .config import MINE_RATE, MINE_YIELDS
from .unloading import depot_room

Yields = tuple[tuple[str, int], ...]


class Mine:

    def __init__(
        self,
        rng: Random,
        yields: Yields = MINE_YIELDS
    ) -> None:
        self.rng = rng
        self.yields = yields      # how often each mineral comes up
        self.dug = 0.             # units, not in the depot yet

    def update(self, stock: Hold, dt: float) -> None:
        if not self.diggable(stock):
            return
        self.dug += MINE_RATE * dt
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
            (name, share) for name, share in self.yields
            if depot_room(stock, name) >= 1
        )
