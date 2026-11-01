""" Fragments flying away from an explosion """

import math
from dataclasses import dataclass
from random import Random

from ..colors import Rgb
from ..config import EXPLOSION_DURATION
from .space import Vec2


@dataclass(slots=True)
class Fragment:
    x: float
    y: float
    vx: float
    vy: float


class Explosion:

    def __init__(
        self,
        rng: Random,
        pos: Vec2,
        velocity: Vec2,
        color: Rgb,
        count: int,
        speed: tuple[float, float],
        duration: float = EXPLOSION_DURATION
    ) -> None:
        self.color = color
        self.duration = duration
        self.age = 0.
        self.fragments = []
        for _ in range(count):
            angle = rng.uniform(0, 2 * math.pi)
            fragment_speed = rng.uniform(*speed)
            self.fragments.append(Fragment(
                pos[0], pos[1],
                velocity[0] + math.cos(angle) * fragment_speed,
                velocity[1] + math.sin(angle) * fragment_speed,
            ))

    @property
    def progress(self) -> float:
        """ From 0 when it starts to 1 when it is over """
        return min(1., self.age / self.duration)

    @property
    def done(self) -> bool:
        return self.age >= self.duration

    def update(self, dt: float) -> None:
        self.age += dt
        for fragment in self.fragments:
            fragment.x += fragment.vx * dt
            fragment.y += fragment.vy * dt

    def shift(self, shift: Vec2) -> None:
        for fragment in self.fragments:
            fragment.x += shift[0]
            fragment.y += shift[1]
