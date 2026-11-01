""" Outposts, built where their site lies by delivering ore from the cargo
of ships landed there, stage after stage: each on a body, in the direction
of the pad ships land on, with the post serving them once built far
enough """

import math
from dataclasses import dataclass, field
from random import Random

from ..mining.ore import Hold, whole_units, withdraw
from ..ship.ground import Ground, pad_edge
from ..ship.parking import Parking
from ..world.space import Celestial, Vec2
from .board import Board, Contracts
from .config import PAD_DIRECTION
from .permits import Permits
from .post import Post, Services
from .sites import SITES, Site, Stage
from .wallet import Wallet


@dataclass(frozen=True)
class Progress:
    """ Of an outpost being built, and trading once it can """
    built: int = 0                      # stages
    delivered: dict[str, int] = field(default_factory=dict)
    stock: Hold = field(default_factory=dict)  # of its depot
    contracts: Contracts = field(default_factory=Contracts)

    @property
    def started(self) -> bool:
        return bool(self.built or self.delivered or self.stock)


class Construction:
    """ An outpost on its site: the stages built, and what was delivered
    for the next one """

    def __init__(self, site: Site, permits: Permits | None = None) -> None:
        self.site = site
        self.permits = permits or Permits()
        self.built = 0                      # stages
        self.delivered: dict[str, int] = {}  # for the next stage

    def restore(self, progress: Progress) -> None:
        self.built = min(progress.built, len(self.site.stages))
        self.delivered = dict(progress.delivered)

    @property
    def stage(self) -> Stage | None:
        """ Being built, None once all are """
        stages = self.site.stages
        return stages[self.built] if self.built < len(stages) else None

    @property
    def services(self) -> Services:
        """ Of the last stage built, nothing before the first """
        if self.built == 0:
            return Services()
        return self.site.stages[self.built - 1].services

    @property
    def locked(self) -> bool:
        """ The stage being built needs a concession not granted yet """
        return self.stage is not None and self.permits.lacks(self.stage.permit)

    @property
    def needed(self) -> dict[str, int]:
        """ Units still to deliver for the stage being built, by mineral """
        if self.stage is None:
            return {}
        lacking = {
            name: units - self.delivered.get(name, 0)
            for name, units in self.stage.materials
        }
        return {name: units for name, units in lacking.items() if units > 0}

    def deliver(self, cargo: Hold) -> Stage | None:
        """ Takes from `cargo` whole units of what is needed. Returns the
        stage built by it, if so. Nothing goes without its concession. """
        if self.locked:
            return None
        for name, units in self.needed.items():
            taken = min(units, whole_units(cargo.get(name, 0.)))
            if taken <= 0:
                continue
            withdraw(cargo, name, taken)
            self.delivered[name] = self.delivered.get(name, 0) + taken
        stage = self.stage
        if stage is None or self.needed:
            return None
        self.built += 1
        self.delivered = {}
        return stage


@dataclass
class Outpost:
    key: str                  # saved under it
    body: Celestial
    direction: float          # of the pad, from the body center
    construction: Construction
    post: Post
    rng: Random
    board: Board | None = None          # its missions, once it can trade

    def open_board(self, wallet: Wallet) -> None:
        """ Its missions, paid into `wallet`: none for sites giving none """
        site = self.construction.site
        if not site.gives_missions:
            self.board = None
            return
        self.board = Board(
            self.rng, wallet, clientele=site.trade.clientele,
        )

    @property
    def name(self) -> str:
        return self.construction.site.name

    @property
    def ground(self) -> Ground:
        site = self.construction.site
        return Ground(
            self.body,
            pad_edge(self.body.radius, self.direction, site.pad_width),
            kind='port' if site.form == 'orbit' else 'pad',
            port_direction=self.direction,
        )

    @property
    def pos(self) -> Vec2:
        """ Of the middle of the pad, on the surface """
        x, y = self.body.pos
        radius = self.body.radius
        return (
            x + math.cos(self.direction) * radius,
            y + math.sin(self.direction) * radius,
        )

    def serves(self, parking: Parking | None) -> bool:
        """ Ships parked on its pad """
        if parking is None or parking.body is not self.body:
            return False
        return self.ground.edge[round(math.degrees(parking.direction)) % 360]

    @property
    def progress(self) -> Progress:
        """ Of its construction, with what its depot holds, and its
        missions """
        board, construction = self.board, self.construction
        return Progress(
            construction.built, dict(construction.delivered),
            dict(self.post.depot.stock),
            board.contracts if board else Contracts(),
        )

    def deliver(self, cargo: Hold) -> Stage | None:
        """ What is needed from `cargo`: the stage built by it, if so """
        built = self.construction.deliver(cargo)
        self.post.services = self.construction.services
        return built

    def restore(self, progress: Progress) -> None:
        self.construction.restore(progress)
        self.post.services = self.construction.services
        stock = self.post.depot.stock
        stock.clear()
        stock.update(progress.stock)
        if self.board is not None:
            self.board.resume(progress.contracts)


def bare_outpost(key: str, body: Celestial, rng: Random,
                 permits: Permits | None = None) -> Outpost:
    """ On its site, nothing built """
    site = SITES[key]
    return Outpost(
        key, body, math.radians(PAD_DIRECTION), Construction(site, permits),
        Post(Services(), rng, site.refinery, site.yields), rng,
    )


def open_boards(outposts: list[Outpost], wallet: Wallet) -> None:
    """ For a game, new or saved """
    for outpost in outposts:
        outpost.open_board(wallet)
