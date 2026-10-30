""" Posts ships land at to be served, the Earth and outposts: what each
offers, its depot, and its work on each frame """

from dataclasses import dataclass
from random import Random

from ..ship.fuel import Tank
from .crushing import Crusher
from .refuel import fill
from .unloading import Depot
from .wallet import Wallet


@dataclass(frozen=True)
class Services:
    """ What a post offers the ships landed there """
    fuel: bool = False        # their tank filled
    depot: bool = False       # their cargo unloaded, kept there
    market: bool = False      # ore of the depot sold
    missions: bool = False
    hangar: bool = False      # parts bought and fitted
    refinery: bool = False    # rock of the depot crushed


EVERYTHING = Services(True, True, True, True, True, True)


@dataclass(frozen=True)
class Docked:
    """ A ship landed at a post, as the post sees it """
    ore: dict[str, float]     # in its cargo
    tank: Tank


class Post:

    def __init__(self, name: str, services: Services, rng: Random) -> None:
        self.name = name
        self.services = services
        self.depot = Depot()
        self.crusher = Crusher(rng)

    def update(self, dt: float, ship: Docked | None,
               wallet: Wallet) -> list[str]:
        """ Fills the tank of a ship landed there, unloads it, and crushes
        rock even without any. Returns what the crushing found. """
        stock = self.depot.stock
        if ship is not None and self.services.fuel:
            fill(ship.tank, wallet, ship.ore, stock)
        self.depot.update(ship.ore if ship else {}, dt, ship is not None)
        if not self.services.refinery:
            return []
        return self.crusher.update(stock, dt)
