""" Unloading the cargo into the depot of a post, where the ship lands
to empty it, and loading it back from there """

from ..mining.minerals import MINERALS
from ..mining.ore import EPSILON, Hold, cargo_load, whole_units, withdraw
from .config import UNLOAD_RATE


def unload(ore: Hold, stock: Hold,
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
    if ore[mineral] <= EPSILON:
        # What rounding left goes along
        stock[mineral] += ore.pop(mineral)
    return mineral


def load(stock: Hold, ore: Hold, mineral: str,
         room: float) -> int:
    """ Whole units of `mineral` back into the cargo, as many as there are
    and as fit in `room`. Returns how many. """
    units = min(whole_units(stock.get(mineral, 0.)), whole_units(room))
    if units <= 0:
        return 0
    withdraw(stock, mineral, units)
    ore[mineral] = ore.get(mineral, 0.) + units
    return units


class Depot:
    """ The stock of a post, filled from the cargo of the ship landed
    there, a bit at a time """

    def __init__(self) -> None:
        self.stock: Hold = {}
        self.unloading = False
        self.mineral: str | None = None      # being unloaded right now

    def start(self, ore: Hold) -> None:
        self.unloading = cargo_load(ore) > 0

    def stop(self) -> None:
        self.unloading = False
        self.mineral = None

    def update(self, ore: Hold, dt: float,
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
