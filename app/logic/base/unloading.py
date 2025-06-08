""" Unloading the cargo into the depot on the Earth, where the ship lands
to empty it """

from ..mining.minerals import MINERALS
from ..mining.ore import cargo_load
from .config import UNLOAD_RATE


def unload(ore: dict[str, float], stock: dict[str, float],
           amount: float) -> str | None:
    """ Move up to `amount` of the cargo into the stock, one mineral after
    the other in the order of the minerals table. Returns the mineral
    moved, None once the cargo is empty. """
    mineral = next((name for name in MINERALS if ore.get(name, 0.) > 0), None)
    if mineral is None:
        return None
    moved = min(amount, ore[mineral])
    stock[mineral] = stock.get(mineral, 0.) + moved
    ore[mineral] -= moved
    if ore[mineral] <= 1e-6:
        # What rounding left goes along
        stock[mineral] += ore.pop(mineral)
    return mineral


class Depot:
    """ The stock on the Earth, filled from the cargo of the ship landed
    there, a bit at a time """

    def __init__(self) -> None:
        self.stock: dict[str, float] = {}
        self.unloading = False
        self.mineral: str | None = None      # being unloaded right now

    def start(self, ore: dict[str, float]) -> None:
        self.unloading = cargo_load(ore) > 0

    def stop(self) -> None:
        self.unloading = False
        self.mineral = None

    def update(self, ore: dict[str, float], dt: float,
               docked: bool) -> None:
        """ Taking off stops unloading """
        if not self.unloading:
            return
        if not docked:
            self.stop()
            return
        self.mineral = unload(ore, self.stock, UNLOAD_RATE * dt)
        if self.mineral is None:
            self.stop()
