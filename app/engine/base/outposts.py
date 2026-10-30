""" Outposts in the solar system: each on its site, a body and the
direction of the pad ships land on, with its construction, and the post
serving the ships there once built far enough """

import math
from dataclasses import dataclass, replace
from random import Random

from ...logic.base.config import PAD_DIRECTION, PAD_WIDTH
from ...logic.base.outposts import SITES, Construction, Stage
from ...logic.base.post import Post, Services
from ...logic.save import Progress
from ...logic.ship.landing import Ground, Parking, pad
from ...logic.world.space import Celestial, Vec2
from ..world.solar_system import SolarSystem


@dataclass
class Outpost:
    key: str                  # saved under it
    body: Celestial
    direction: float          # of the pad, from the body center
    construction: Construction
    post: Post

    @property
    def name(self) -> str:
        return self.construction.site.name

    @property
    def ground(self) -> Ground:
        return Ground(self.body, pad(self.body.radius, self.direction,
                                     PAD_WIDTH))

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
        """ Of its construction, with what its depot holds """
        return replace(
            self.construction.progress, stock=dict(self.post.depot.stock),
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


def found(system: SolarSystem, rng: Random) -> list[Outpost]:
    """ On their sites, nothing built yet: the Frontier on the farthest
    planet """
    site = SITES['frontier']
    return [Outpost(
        'frontier', system.planets[-1], math.radians(PAD_DIRECTION),
        Construction(site), Post(site.name, Services(), rng),
    )]
