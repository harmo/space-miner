""" Swarms of rich asteroids, passing through the solar system now and
then, between the orbits of the planets """

import math
from collections.abc import Sequence
from dataclasses import dataclass
from random import Random
from typing import Literal

from .config import (
    SWARM_ASTEROIDS,
    SWARM_EVERY,
    SWARM_RADIUS,
    SWARM_SPREAD,
    SWARM_STAYS,
    SWARM_WIDTH,
)
from .layout import OrbiterPlan, orbital_speed, plan_asteroid

# Hardly any in the belts
RICH = (
    'gold', 'crystal', 'uranium', 'helium3', 'ruby', 'nebulite',
    'stellarium', 'antimatter',
)
Change = Literal['arrives', 'leaves']


@dataclass(frozen=True)
class SwarmPlan:
    distance: float           # of its middle to the sun
    asteroids: tuple[OrbiterPlan, ...]


def plan_swarm(rng: Random, orbits: Sequence[float]) -> SwarmPlan:
    """ Gathered on an orbit halfway between two of the `orbits`, those of
    the planets and of the belt around the sun """
    gap = rng.randrange(len(orbits) - 1)
    middle = (orbits[gap] + orbits[gap + 1]) / 2
    angle = rng.uniform(0, 2 * math.pi)
    spread = math.radians(SWARM_SPREAD) / 2
    asteroids = []
    for _ in range(SWARM_ASTEROIDS):
        distance = middle + rng.uniform(-.5, .5) * SWARM_WIDTH
        asteroids.append(plan_asteroid(
            rng, distance, orbital_speed(distance) * rng.uniform(.97, 1.03),
            angle + rng.uniform(-spread, spread), RICH, SWARM_RADIUS,
        ))
    return SwarmPlan(middle, tuple(asteroids))


class SwarmClock:
    """ When swarms come, and when they leave """

    def __init__(self, rng: Random) -> None:
        self.rng = rng
        self.waiting = rng.uniform(*SWARM_EVERY)
        self.left = 0.            # before the swarm there leaves

    @property
    def passing(self) -> bool:
        return self.left > 0

    def update(self, dt: float) -> Change | None:
        if self.passing:
            self.left -= dt
            if self.left <= 0:
                self.left = 0.
                self.waiting = self.rng.uniform(*SWARM_EVERY)
                return 'leaves'
            return None
        self.waiting -= dt
        if self.waiting <= 0:
            self.left = SWARM_STAYS
            return 'arrives'
        return None
