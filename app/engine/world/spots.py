""" Places markers and the map point at: the middle of a group of
asteroids passing by """

from collections.abc import Sequence
from dataclasses import dataclass

from ...logic.world.space import Celestial, Vec2

GROUP_SIZE = 300.             # around its middle, for its marker


@dataclass(frozen=True)
class Spot:
    """ Somewhere to point at """
    pos: Vec2
    radius: float


def spot_of(asteroids: Sequence[Celestial]) -> Spot | None:
    """ Their middle, None without any """
    if not asteroids:
        return None
    count = len(asteroids)
    return Spot((
        sum(asteroid.pos[0] for asteroid in asteroids) / count,
        sum(asteroid.pos[1] for asteroid in asteroids) / count,
    ), GROUP_SIZE)
