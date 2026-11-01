""" Comets, passing through the solar system now and then on very long
ellipses, slow at their far end and racing by the sun, as Kepler said """

import math
from collections.abc import Sequence
from random import Random

from .config import (
    COMET_EVERY,
    COMET_PERIHELION,
    COMET_TAIL,
    COMET_TAIL_RANGE,
    COMET_TIME,
)
from .space import Celestial, Orbit, Vec2

SOLVING = 12                  # steps, Newton's method on Kepler's equation


class CometOrbit(Orbit):
    """ From one far end of its ellipse to the other, the parent on one
    of its foci. `anomaly` goes from -pi to pi, 0 being closest to it. """

    def __init__(self, parent: Celestial, closest: float, farthest: float,
                 time: float, tilt: float, sense: int) -> None:
        super().__init__(parent, (closest + farthest) / 2, 0., 0.)
        self.eccentricity = (farthest - closest) / (farthest + closest)
        self.minor = self.radius * math.sqrt(1 - self.eccentricity ** 2)
        self.motion = 2 * math.pi / time
        self.tilt = tilt
        self.sense = sense        # 1 counterclockwise, -1 clockwise
        self.anomaly = -math.pi
        self.along = self.solved()

    def solved(self) -> float:
        """ The angle along the ellipse, from Kepler's equation """
        along = math.pi if self.anomaly >= 0 else -math.pi
        for _ in range(SOLVING):
            along -= (
                along - self.eccentricity * math.sin(along) - self.anomaly
            ) / (1 - self.eccentricity * math.cos(along))
        return along

    def advance(self, dt: float) -> None:
        self.anomaly += self.motion * dt
        self.along = self.solved()

    def turned(self, x: float, y: float) -> Vec2:
        cos, sin = math.cos(self.tilt), math.sin(self.tilt)
        y *= self.sense
        return x * cos - y * sin, x * sin + y * cos

    def at(self, along: float) -> Vec2:
        """ At that angle along the ellipse """
        x, y = self.turned(
            self.radius * (math.cos(along) - self.eccentricity),
            self.minor * math.sin(along),
        )
        parent_x, parent_y = self.parent.pos
        return parent_x + x, parent_y + y

    @property
    def position(self) -> Vec2:
        return self.at(self.along)

    @property
    def velocity(self) -> Vec2:
        pace = self.motion / (1 - self.eccentricity * math.cos(self.along))
        vx, vy = self.turned(
            -self.radius * math.sin(self.along) * pace,
            self.minor * math.cos(self.along) * pace,
        )
        parent_vx, parent_vy = self.parent.velocity
        return parent_vx + vx, parent_vy + vy

    @property
    def over(self) -> bool:
        """ Back at the far end, leaving the solar system """
        return self.anomaly >= math.pi

    @property
    def until_closest(self) -> float:
        """ Seconds, negative once past the sun """
        return -self.anomaly / self.motion

    @property
    def left(self) -> float:
        """ Seconds before leaving the solar system """
        return (math.pi - self.anomaly) / self.motion

    def path(self, points: int) -> list[Vec2]:
        """ Its whole ellipse """
        return [
            self.at(2 * math.pi * index / points)
            for index in range(points + 1)
        ]


def plan_comet(rng: Random, sun: Celestial,
               orbits: Sequence[float]) -> CometOrbit:
    """ From as far as the last planet, whichever the way """
    return CometOrbit(
        sun, sun.radius + COMET_PERIHELION, orbits[-1], COMET_TIME,
        rng.uniform(0, 2 * math.pi), rng.choice((-1, 1)),
    )


def tail_length(distance: float) -> float:
    """ At `distance` from the sun surface: longer the closer it gets """
    closeness = max(0., 1 - distance / COMET_TAIL_RANGE)
    return float(COMET_TAIL * closeness ** 1.5)


class CometClock:
    """ When the next comet comes """

    def __init__(self, rng: Random) -> None:
        self.rng = rng
        self.waiting = rng.uniform(*COMET_EVERY)

    def due(self, dt: float) -> bool:
        self.waiting -= dt
        if self.waiting > 0:
            return False
        self.waiting = self.rng.uniform(*COMET_EVERY)
        return True
