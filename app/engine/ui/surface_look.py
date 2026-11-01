""" What is built on bodies is drawn with: steel, glass and blinking lights,
laid along the curve of the surface """

import math
import time

from ...logic.world.space import Celestial, Vec2, polar

STEEL = (.42, .47, .54)
DARK = (.16, .18, .22)
GLASS = (.7, .82, .9)
BLINK = 1.2                   # seconds, of the lights
SEEN = 2000.                  # drawn only this close to the camera
STEP = 8.                     # pixels, between points of long shapes


class Frame:
    """ On the surface, `along` it from `direction`, the middle of what is
    drawn, and `up` from it, in pixels """

    def __init__(self, body: Celestial, direction: float) -> None:
        self.center = body.pos
        self.radius = body.radius
        self.direction = direction

    def at(self, along: float, up: float) -> Vec2:
        angle = self.direction + along / self.radius
        return polar(self.center, angle, self.radius + up)

    def box(
        self,
        left: float,
        right: float,
        top: float,
        bottom: float = -3.
    ) -> tuple[list[Vec2], list[Vec2]]:
        """ Its lower and upper edges, bending with the surface: sunk a
        little into the ground, not to float above it """
        steps = max(1, math.ceil((right - left) / STEP))
        alongs = [left + (right - left) * k / steps for k in range(steps + 1)]
        return (
            [self.at(along, bottom) for along in alongs],
            [self.at(along, top) for along in alongs],
        )


def blinking(phase: float) -> float:
    """ From faint to bright, `phase` from 0 to 1 along the blink """
    return .3 + .7 * (.5 + .5 * math.cos(
        2 * math.pi * (time.monotonic() / BLINK + phase)
    ))
