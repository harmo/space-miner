""" The scanner of the ship: which asteroids it finds within its reach,
of the minerals it looks for """

import math
from collections.abc import Collection, Sequence

from ..mining.minerals import MINED
from ..world.space import Celestial, Vec2

# Looked for unless chosen otherwise: anything worth more than rock
LOOKED_FOR = [name for name in MINED if name != 'rock']


def mineral_of(asteroid: Celestial) -> str:
    return asteroid.mineral or 'rock'


def within(asteroids: Sequence[Celestial], pos: Vec2,
           reach: float) -> list[Celestial]:
    """ Closest first """
    found = [
        asteroid for asteroid in asteroids
        if math.dist(pos, asteroid.pos) <= reach
    ]
    return sorted(found, key=lambda asteroid: math.dist(pos, asteroid.pos))


def found(asteroids: Sequence[Celestial], pos: Vec2, reach: float,
          looked_for: Collection[str], count: int) -> list[Celestial]:
    """ The `count` closest of the minerals looked for """
    return [
        asteroid for asteroid in within(asteroids, pos, reach)
        if mineral_of(asteroid) in looked_for
    ][:count]


def counts(asteroids: Sequence[Celestial], pos: Vec2,
           reach: float) -> dict[str, int]:
    """ Asteroids within reach, by mineral """
    counted = dict.fromkeys(MINED, 0)
    for asteroid in within(asteroids, pos, reach):
        counted[mineral_of(asteroid)] += 1
    return counted
