""" Fuel on the Earth: the tank of the ship landed there is filled with
ice first, from its cargo then from the depot, then with credits, as far
as they go, and up to a small reserve for free. A ship out of fuel far
away is towed back, for a price growing with the distance. """

import math
from dataclasses import dataclass

from ..ship.fuel import Tank
from .config import FREE_RESERVE, FUEL_PRICE, ICE_FUEL, TOW_BASE, TOW_RATE
from .wallet import Wallet


@dataclass(frozen=True)
class Refuel:
    ice: float                # units taken from the holds
    credits: int              # paid
    fuel: float               # put in the tank


def take_ice(wanted: float, holds: tuple[dict[str, float], ...]) -> float:
    """ Up to `wanted` units, from one hold after the other """
    taken = 0.
    for hold in holds:
        ice = min(hold.get('ice', 0.), wanted - taken)
        if ice > 0:
            hold['ice'] -= ice
            if hold['ice'] <= 1e-6:
                del hold['ice']
            taken += ice
    return taken


def refuel(missing: float, wallet: Wallet,
           *holds: dict[str, float]) -> Refuel:
    """ Up to `missing` units of fuel, taking the ice of the holds then
    credits """
    ice = take_ice(missing / ICE_FUEL, holds)
    fuel = ice * ICE_FUEL
    cost = min(math.ceil((missing - fuel) * FUEL_PRICE - 1e-9),
               wallet.credits)
    if cost > 0:
        wallet.pay(cost)
        fuel = min(missing, fuel + cost / FUEL_PRICE)
    return Refuel(ice, max(0, cost), fuel)


def fill(tank: Tank, wallet: Wallet, *holds: dict[str, float]) -> Refuel:
    """ As full as the ice and credits allow, and the reserve at least """
    done = refuel(tank.missing, wallet, *holds)
    tank.fill(done.fuel)
    tank.level = max(tank.level, tank.capacity * FREE_RESERVE)
    return done


def tow_price(distance: float) -> int:
    """ Back to the Earth, from `distance` away """
    return round(TOW_BASE + distance * TOW_RATE)


def tow(price: int, wallet: Wallet) -> int:
    """ Paid as far as the credits go, returns how much """
    paid = min(price, wallet.credits)
    wallet.pay(paid)
    return paid
