""" What ore is worth: paid well by the missions, poorly by the market of
the base, which buys from the depot """

import math

from ..mining.minerals import MINERALS, Mineral
from ..mining.ore import whole_units
from .config import ORE_SALE
from .wallet import Wallet


def ore_value(mineral: Mineral) -> float:
    """ Credits for a unit: harder to mine and rarer is worth more. What
    no asteroid holds is as common as rock. """
    rock = MINERALS['rock']
    return 5 * mineral.hardness * math.sqrt(
        rock.frequency / (mineral.frequency or rock.frequency)
    )


def ore_price(name: str) -> int:
    """ Paid by the market for a unit """
    return max(1, round(ore_value(MINERALS[name]) * ORE_SALE))


def sell_ore(stock: dict[str, float], name: str, units: int,
             wallet: Wallet) -> int:
    """ Sells up to `units` whole units of the stock, returns how many """
    sold = min(units, whole_units(stock.get(name, 0.)))
    if sold <= 0:
        return 0
    stock[name] -= sold
    if stock[name] <= 1e-6:
        del stock[name]
    wallet.earn(sold * ore_price(name))
    return sold
