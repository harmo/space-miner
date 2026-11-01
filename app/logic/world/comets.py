""" Comets, passing through the solar system now and then on very long
ellipses, slow at their far end and racing by the sun, as Kepler said """

import math
from collections.abc import Sequence
from dataclasses import dataclass
from random import Random

from .config import (
    COMET_DEBRIS,
    COMET_DEBRIS_ORBIT,
    COMET_DEBRIS_SPEED,
    COMET_EVERY,
    COMET_ICE,
    COMET_PERIHELION,
    COMET_TAIL,
    COMET_TAIL_RANGE,
    COMET_TIME,
)
from .layout import OrbiterPlan, plan_asteroid
from .space import Celestial, Orbit, Vec2
from .swarms import RICH

SOLVING = 12                  # steps, Newton's method on Kepler's equation
# What it sheds: ice, then the richer the closer to the sun
ICE = ('ice',)
THAWING = ('ice', 'gold', 'crystal', 'helium3')


@dataclass(frozen=True)
class CometPath:
    closest: float            # to the sun
    farthest: float
    time: float               # seconds, from one far end to the other
    tilt: float               # of its long axis
    sense: int                # 1 counterclockwise, -1 clockwise


class CometOrbit(Orbit):
    """ From one far end of its ellipse to the other, the parent on one
    of its foci. `anomaly` goes from -pi to pi, 0 being closest to it. """

    def __init__(self, parent: Celestial, path: CometPath) -> None:
        closest, farthest = path.closest, path.farthest
        super().__init__(parent, (closest + farthest) / 2, 0., 0.)
        self.eccentricity = (farthest - closest) / (farthest + closest)
        self.minor = self.radius * math.sqrt(1 - self.eccentricity ** 2)
        self.motion = 2 * math.pi / path.time
        self.tilt = path.tilt
        self.sense = path.sense
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
        self.set_anomaly(self.anomaly + self.motion * dt)

    def set_anomaly(self, anomaly: float) -> None:
        self.anomaly = anomaly
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


def plan_comet(
    rng: Random,
    sun: Celestial,
    orbits: Sequence[float]
) -> CometPath:
    """ From as far as the last planet, whichever the way """
    return CometPath(
        sun.radius + COMET_PERIHELION, orbits[-1], COMET_TIME,
        rng.uniform(0, 2 * math.pi), rng.choice((-1, 1)),
    )


def thaw(distance: float) -> float:
    """ From 0 far from the sun, to 1 on its surface """
    return float(max(0., 1 - distance / COMET_TAIL_RANGE) ** 1.5)


def tail_length(distance: float) -> float:
    """ At `distance` from the sun surface: longer the closer it gets """
    return COMET_TAIL * thaw(distance)


def debris_shed(distance: float) -> int:
    """ Asteroids around it once at `distance` from the sun surface, as
    the sun thaws it """
    return COMET_ICE + round(COMET_DEBRIS * thaw(distance))


def plan_debris(rng: Random, count: int) -> OrbiterPlan:
    """ The next one around it, `count` of them being there: richer and
    richer, as the sun thaws it deeper """
    extra = count - COMET_ICE
    minerals = (
        ICE if extra < 0 else THAWING if extra < COMET_DEBRIS / 2 else RICH
    )
    return plan_asteroid(
        rng, rng.uniform(*COMET_DEBRIS_ORBIT),
        rng.uniform(*COMET_DEBRIS_SPEED), minerals=minerals,
    )


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
