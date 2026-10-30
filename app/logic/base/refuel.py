""" Fuel on the Earth: the tank of the ship landed there is filled with the
ice of the depot first, then with credits, as far as they go. A ship out of
fuel far away is towed back, for a price growing with the distance. """

import math
from dataclasses import dataclass

from .config import FUEL_PRICE, ICE_FUEL, TOW_BASE, TOW_RATE
from .wallet import Wallet


@dataclass(frozen=True)
class Refuel:
    ice: float                # units taken from the depot
    credits: int              # paid
    fuel: float               # put in the tank


def refuel(missing: float, stock: dict[str, float],
           wallet: Wallet) -> Refuel:
    """ Up to `missing` units of fuel, taking the ice and credits """
    ice = min(stock.get('ice', 0.), missing / ICE_FUEL)
    if ice > 0:
        stock['ice'] -= ice
        if stock['ice'] <= 1e-6:
            del stock['ice']
    fuel = ice * ICE_FUEL
    cost = min(math.ceil((missing - fuel) * FUEL_PRICE - 1e-9),
               wallet.credits)
    if cost > 0:
        wallet.pay(cost)
        fuel = min(missing, fuel + cost / FUEL_PRICE)
    return Refuel(ice, max(0, cost), fuel)


def tow_price(distance: float) -> int:
    """ Back to the Earth, from `distance` away """
    return round(TOW_BASE + distance * TOW_RATE)


def tow(price: int, wallet: Wallet) -> int:
    """ Paid as far as the credits go, returns how much """
    paid = min(price, wallet.credits)
    wallet.pay(paid)
    return paid
