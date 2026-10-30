""" Solar flares, now and then: the sun warns, then blazes, heating all
around it much more, and leaves ejecta of the rarest ore on low orbits,
which fall back into it a few minutes later """

import math
from random import Random
from typing import Literal

from .config import (
    EJECTA_ASTEROIDS,
    EJECTA_ORBIT,
    EJECTA_RADIUS,
    EJECTA_SPREAD,
    EJECTA_STAYS,
    FLARE_BLAZE,
    FLARE_EVERY,
    FLARE_SURGE,
    FLARE_WARNING,
)
from .layout import OrbiterPlan, orbital_speed, plan_asteroid

# Found nowhere else in such quantities
RICHEST = ('nebulite', 'stellarium', 'antimatter')
Phase = Literal['quiet', 'warning', 'blazing', 'ejecta']
Change = Literal['warns', 'blazes', 'ejects', 'falls']


def plan_ejecta(rng: Random, sun_radius: float) -> tuple[OrbiterPlan, ...]:
    """ Thrown out together, along an arc of low orbits """
    middle = rng.uniform(0, 2 * math.pi)
    spread = math.radians(EJECTA_SPREAD) / 2
    low, high = EJECTA_ORBIT
    asteroids = []
    for _ in range(EJECTA_ASTEROIDS):
        distance = sun_radius + rng.uniform(low, high)
        asteroids.append(plan_asteroid(
            rng, distance, orbital_speed(distance),
            middle + rng.uniform(-spread, spread), RICHEST, EJECTA_RADIUS,
        ))
    return tuple(asteroids)


class FlareClock:
    """ From one phase to the next: quiet, warning, blazing, then the
    ejecta, and quiet again """

    def __init__(self, rng: Random) -> None:
        self.rng = rng
        self.phase: Phase = 'quiet'
        self.left = rng.uniform(*FLARE_EVERY)   # seconds, of the phase

    @property
    def lasts(self) -> float:
        """ Seconds of the whole phase """
        return {
            'warning': FLARE_WARNING, 'blazing': FLARE_BLAZE,
            'ejecta': EJECTA_STAYS,
        }.get(self.phase, FLARE_EVERY[1])

    @property
    def progress(self) -> float:
        """ Of the phase, from 0 to 1 """
        return min(1., max(0., 1 - self.left / self.lasts))

    @property
    def surge(self) -> float:
        """ Times the heat of the sun: rising, then falling, while it
        blazes """
        if self.phase != 'blazing':
            return 1.
        return 1 + (FLARE_SURGE - 1) * math.sin(math.pi * self.progress)

    def update(self, dt: float) -> Change | None:
        self.left -= dt
        if self.left > 0:
            return None
        if self.phase == 'quiet':
            self.phase, self.left = 'warning', FLARE_WARNING
            return 'warns'
        if self.phase == 'warning':
            self.phase, self.left = 'blazing', FLARE_BLAZE
            return 'blazes'
        if self.phase == 'blazing':
            self.phase, self.left = 'ejecta', EJECTA_STAYS
            return 'ejects'
        self.phase, self.left = 'quiet', self.rng.uniform(*FLARE_EVERY)
        return 'falls'
