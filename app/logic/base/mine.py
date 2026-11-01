""" The mine of an outpost, digging on its own into the depot, whether a
ship is there or not, for as long as the game runs and the depot has room
"""

from random import Random

from ..mining.ore import Hold
from .config import MINE_RATE, MINE_YIELDS
from .unloading import depot_room


class Mine:

    def __init__(self, rng: Random) -> None:
        self.rng = rng
        self.dug = 0.             # units, not in the depot yet

    def update(self, stock: Hold, dt: float) -> None:
        if depot_room(stock) < 1:
            return
        self.dug += MINE_RATE * dt
        names = [name for name, _ in MINE_YIELDS]
        weights = [share for _, share in MINE_YIELDS]
        while self.dug >= 1 and depot_room(stock) >= 1:
            self.dug -= 1
            mineral = self.rng.choices(names, weights)[0]
            stock[mineral] = stock.get(mineral, 0.) + 1
