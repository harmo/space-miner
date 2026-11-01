""" Posts ships land at to be served, the Earth and outposts: what each
offers, its depot, and its work on each frame """

from dataclasses import dataclass
from random import Random

from ..mining.ore import Hold, cargo_total
from ..ship.fuel import Tank
from ..ship.heat import HullHeat
from .board import Board
from .config import MINE_YIELDS
from .crushing import PLAIN_REFINERY, Crusher, Refinery
from .mine import Mine, Yields
from .refuel import fill
from .shuttles import Shuttle
from .unloading import Depot
from .wallet import Wallet


@dataclass(frozen=True)
class Services:
    """ What a post offers the ships landed there """
    fuel: bool = False        # their tank filled
    depot: bool = False       # their cargo unloaded, kept there
    market: bool = False      # ore of the depot sold
    missions: bool = False
    refinery: bool = False    # rock of the depot crushed
    shelter: bool = False     # their hull cooled, out of the heat
    mine: bool = False        # ore dug into the depot
    dock: bool = False        # a shuttle, carrying ore of the depot away


HOME_SERVICES = Services(
    fuel=True, depot=True, market=True, missions=True, refinery=True,
    dock=True,
)


@dataclass(frozen=True)
class Docked:
    """ A ship landed at a post, as the post sees it """
    ore: Hold     # in its cargo
    tank: Tank
    heat: HullHeat


@dataclass(frozen=True)
class PostStatus:
    """ What a post tells, right now """
    unloading: bool
    crushing: bool
    can_unload: bool          # a cargo into its depot
    to_validate: bool         # a mission, from its depot and the cargo
    full: bool                # its depot, for what the cargo holds


class Post:

    def __init__(
        self,
        services: Services,
        rng: Random,
        refinery: Refinery = PLAIN_REFINERY,
        yields: Yields = MINE_YIELDS
    ) -> None:
        self.services = services
        self.depot = Depot()
        self.crusher = Crusher(rng, refinery)
        self.mine = Mine(rng, yields)
        self.shuttle = Shuttle()

    def status(
        self,
        cargo: Hold,
        board: Board | None
    ) -> PostStatus:
        """ `board` holding its missions, if it gives any """
        depot = self.depot
        return PostStatus(
            depot.unloading, self.crusher.crushing,
            self.services.depot and not depot.unloading
            and depot.takes(cargo) and cargo_total(cargo) > 0,
            board is not None and any(
                mission.can_validate(depot.stock, cargo)
                for mission in board.active
            ),
            cargo_total(cargo) > 0 and not depot.takes(cargo),
        )

    def update(
        self,
        dt: float,
        ship: Docked | None,
        wallet: Wallet
    ) -> list[str]:
        """ Fills the tank of a ship landed there, cools its hull down in
        a shelter, unloads it, and digs ore and crushes rock even without
        any. Returns what the crushing found. """
        stock = self.depot.stock
        if ship is not None and self.services.fuel:
            fill(ship.tank, wallet, ship.ore, stock)
        if ship is not None and self.services.shelter:
            ship.heat.shelter(dt)
        self.depot.update(ship.ore if ship else {}, dt, ship is not None)
        if self.services.mine:
            self.mine.update(stock, dt)
        if not self.services.refinery:
            return []
        return self.crusher.update(stock, dt)


def home_post(rng: Random) -> Post:
    """ The Earth """
    return Post(HOME_SERVICES, rng)
