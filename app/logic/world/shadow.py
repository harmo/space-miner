""" The shadow a planet casts away from the sun: a cone narrowing down to
a point, where no heat comes, whatever the sun does """

import math
from typing import NamedTuple

from .config import SHADOW_LENGTH
from .space import Vec2


class Shadow(NamedTuple):
    left: Vec2
    right: Vec2
    tip: Vec2

    def covers(self, pos: Vec2) -> bool:
        """ On the same side of its three edges """
        sides = [
            side(start, end, pos) for start, end in (
                (self.left, self.right), (self.right, self.tip),
                (self.tip, self.left),
            )
        ]
        return all(value >= 0 for value in sides) or all(
            value <= 0 for value in sides
        )


def side(start: Vec2, end: Vec2, pos: Vec2) -> float:
    """ Which side of the line from `start` to `end` lies `pos` """
    return (end[0] - start[0]) * (pos[1] - start[1]) - (
        end[1] - start[1]
    ) * (pos[0] - start[0])


def shadow_of(pos: Vec2, radius: float, sun: Vec2) -> Shadow:
    """ Of a planet of `radius` at `pos`, as wide as it is at first """
    dx, dy = pos[0] - sun[0], pos[1] - sun[1]
    distance = math.hypot(dx, dy)
    away_x, away_y = dx / distance, dy / distance
    return Shadow(
        (pos[0] - away_y * radius, pos[1] + away_x * radius),
        (pos[0] + away_y * radius, pos[1] - away_x * radius),
        (pos[0] + away_x * SHADOW_LENGTH, pos[1] + away_y * SHADOW_LENGTH),
    )
