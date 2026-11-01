""" What ore is worth: paid well by the missions, poorly by the market of
the base, which buys from the depot """

import math

from ..mining.minerals import MINERALS, Mineral
from ..mining.ore import Hold, whole_units, withdraw
from .config import ORE_SALE
from .wallet import Wallet


def ore_value(mineral: Mineral) -> float:
    """ Credits for a unit: harder to mine and rarer is worth more. What
    no asteroid holds is as common as rock. """
    rock = MINERALS['rock']
    return 5 * mineral.hardness * math.sqrt(
        rock.frequency / (mineral.frequency or rock.frequency)
    )


def ore_price(name: str, factor: float = 1.) -> int:
    """ Paid by the market for a unit, `factor` times what the Earth pays """
    return max(1, round(ore_value(MINERALS[name]) * ORE_SALE * factor))


def sell_ore(
    stock: Hold,
    name: str,
    units: int,
    wallet: Wallet,
    factor: float = 1.
) -> int:
    """ Sells up to `units` whole units of the stock, returns how many """
    sold = min(units, whole_units(stock.get(name, 0.)))
    if sold <= 0:
        return 0
    withdraw(stock, name, sold)
    wallet.earn(sold * ore_price(name, factor))
    return sold
