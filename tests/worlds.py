""" A planet to land on, and a ship the size of the old one """

import math

from app.logic.world.space import Celestial, Orbit, Vec2

SHIP_LENGTH = 40.
SHIP_WIDTH = 25.
SIZE = (SHIP_LENGTH, SHIP_WIDTH)


def earth() -> Celestial:
    sun = Celestial(0, 600.)
    return Celestial(1, 200., orbit=Orbit(sun, 5400., 25., 0.))


def around(planet: Celestial, direction_degrees: float,
           distance: float) -> Vec2:
    x, y = planet.pos
    angle = math.radians(direction_degrees)
    return x + math.cos(angle) * distance, y + math.sin(angle) * distance
