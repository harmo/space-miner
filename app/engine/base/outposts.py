""" Outposts in the solar system: each on its site, a body and the
direction of the pad ships land on, with its construction, and the post
serving the ships there once built far enough """

import math
from dataclasses import dataclass, replace
from random import Random

from ...logic.base.config import PAD_DIRECTION
from ...logic.base.missions import Board
from ...logic.base.outposts import SITES, Construction, Stage
from ...logic.base.post import Post, Services
from ...logic.base.reputation import Standing
from ...logic.base.wallet import Wallet
from ...logic.save import Progress
from ...logic.ship.landing import Ground, Parking, pad_edge
from ...logic.world.layout import plan_ceres, plan_station
from ...logic.world.space import Celestial, Vec2
from ..world.solar_system import SolarSystem


@dataclass
class Outpost:
    key: str                  # saved under it
    body: Celestial
    direction: float          # of the pad, from the body center
    construction: Construction
    post: Post
    rng: Random
    board: Board | None = None          # its missions, once it can trade

    def open_board(self, wallet: Wallet, standing: Standing) -> None:
        """ Its missions, paid into `wallet`, making the same reputation
        as those of the Earth: none for sites giving none """
        site = self.construction.site
        if not site.gives_missions:
            self.board = None
            return
        trade = site.trade
        self.board = Board(
            self.rng, wallet, standing, trade.clients, trade.bonus,
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
        board = self.board
        return replace(
            self.construction.progress, stock=dict(self.post.depot.stock),
            offers=list(board.offers) if board else [],
            active=list(board.active) if board else [],
            mission_level=board.level if board else 1,
        )

    def deliver(self, cargo: dict[str, float]) -> Stage | None:
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
        board = self.board
        if board is not None:
            board.level = max(1, min(progress.mission_level, board.tier))
            board.active[:] = progress.active
            board.offers[:] = progress.offers
            board.top_up()


def found_outposts(system: SolarSystem, rng: Random) -> list[Outpost]:
    """ On their sites, nothing built yet: the Frontier on the farthest
    planet, Cérès in the belt around the sun, and Icare orbiting the
    first planet, both added to the system """
    earth = system.earth.orbit
    ceres = system.add_body(plan_ceres(
        system.orbits, earth.angle if earth else 0.,
    ))
    first = system.planets[0]
    icare = system.add_body(plan_station(first.radius), first)
    return [
        bare_outpost(key, body, rng) for key, body in (
            ('frontier', system.planets[-1]), ('ceres', ceres),
            ('icare', icare),
        )
    ]


def bare_outpost(key: str, body: Celestial, rng: Random) -> Outpost:
    """ On its site, nothing built """
    site = SITES[key]
    return Outpost(
        key, body, math.radians(PAD_DIRECTION), Construction(site),
        Post(Services(), rng), rng,
    )


def open_boards(outposts: list[Outpost], wallet: Wallet,
                standing: Standing) -> None:
    """ For a game, new or saved """
    for outpost in outposts:
        outpost.open_board(wallet, standing)
