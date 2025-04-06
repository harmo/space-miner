""" What the interface shows, computed without Kivy: markers pointing to
places out of the screen, dotted orbits, the heat of the sun, the cargo
bar, the glow of the shortcut, and when to be compact as on phones """

import math

from .config import (
    MARKER_FAR,
    MARKER_LENGTH,
    MARKER_NEAR,
)
from .world.space import Vec2


def is_on_screen(offset: Vec2, radius: float, half_size: Vec2) -> bool:
    """ Whether a body of `radius` at `offset` from the screen center is at
    least partly visible """
    return (
        abs(offset[0]) - radius < half_size[0]
        and abs(offset[1]) - radius < half_size[1]
    )


def edge_point(direction: float, half_size: Vec2) -> tuple[Vec2, bool]:
    """ Where a ray from the screen center leaves the screen, relative to
    the center, and whether that is on a side edge rather than on the top or
    bottom one """
    cos, sin = math.cos(direction), math.sin(direction)
    to_side = half_size[0] / abs(cos) if cos else math.inf
    to_top = half_size[1] / abs(sin) if sin else math.inf
    if to_side <= to_top:
        return (math.copysign(half_size[0], cos), sin * to_side), True
    return (cos * to_top, math.copysign(half_size[1], sin)), False


def marker_length(distance: float) -> float:
    """ Grows from the shortest to the longest as the target gets closer """
    shortest, longest = MARKER_LENGTH
    closeness = (MARKER_FAR - distance) / (MARKER_FAR - MARKER_NEAR)
    return shortest + (longest - shortest) * min(1., max(0., closeness))
