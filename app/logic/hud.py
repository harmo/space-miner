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


def orbit_dots(center: Vec2, radius: float, view_center: Vec2,
               half_size: Vec2, spacing: float,
               hidden: tuple[Vec2, float] | None = None) -> list[Vec2]:
    """ Dots of a circular orbit inside the view, `spacing` apart. They are
    fixed on the orbit, so they don't slide as the view moves. No dot
    within `hidden`: a (position, radius) disc. """
    distance = math.dist(center, view_center)
    half_diagonal = math.hypot(*half_size)
    if abs(distance - radius) > half_diagonal:
        return []

    count = max(3, round(2 * math.pi * radius / spacing))
    step = 2 * math.pi / count
    if radius <= half_diagonal or distance <= half_diagonal:
        indices = range(count)
    else:
        middle = math.atan2(
            view_center[1] - center[1], view_center[0] - center[0]
        )
        half_span = min(math.pi, half_diagonal / radius * 1.1)
        indices = range(
            math.floor((middle - half_span) / step),
            math.ceil((middle + half_span) / step) + 1,
        )

    dots = []
    for index in indices:
        angle = index * step
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        if (
            abs(x - view_center[0]) > half_size[0]
            or abs(y - view_center[1]) > half_size[1]
        ):
            continue
        if hidden is not None and math.dist((x, y), hidden[0]) < hidden[1]:
            continue
        dots.append((x, y))
    return dots
