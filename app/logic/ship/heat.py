""" Heat of the hull: the sun heats the ship more and more as it gets
closer, and the hull cools down all the time. Too hot, the ship blows up.
Shields stop part of the heat. """

import math
from dataclasses import dataclass
from typing import Literal

from ..config import HEAT_RANGE
from ..world.space import Vec2
from .config import (
    HEAT_COOLING,
    HEAT_GAIN,
    HOT,
    OVERHEATING,
    SHELTER_COOLING,
)

Warmth = Literal['cool', 'hot', 'overheating']


def sun_heat(distance: float) -> float:
    """ From 0 out of HEAT_RANGE from the sun surface, to 1 on it: slowly
    at first, then faster and faster """
    closeness = min(1., max(0., 1. - distance / HEAT_RANGE))
    return closeness ** 2


def heating(distance: float, shield: float = 0.,
            surge: float = 1.) -> float:
    """ A second, at `distance` from the sun surface, `shield` the part of
    the heat stopped, `surge` times more during flares """
    return HEAT_GAIN * sun_heat(distance) * surge * (1 - shield)


@dataclass(frozen=True)
class Sunlight:
    """ What heats the hull """
    pos: Vec2                 # of the sun
    radius: float
    surge: float = 1.         # times more during flares

    def distance(self, pos: Vec2) -> float:
        """ From the sun surface """
        return math.dist(pos, self.pos) - self.radius


class Hull:

    def __init__(self) -> None:
        self.heat = 0.                      # from cool to blowing up

    @property
    def burnt(self) -> bool:
        return self.heat >= 1.

    @property
    def warmth(self) -> Warmth:
        if self.heat >= OVERHEATING:
            return 'overheating'
        return 'hot' if self.heat >= HOT else 'cool'

    def update(self, dt: float, heating: float) -> None:
        self.heat = min(1., max(0., self.heat + (heating - HEAT_COOLING) * dt))

    def shelter(self, dt: float) -> None:
        """ Out of the heat, cooling down fast """
        self.heat = max(0., self.heat - SHELTER_COOLING * dt)

    def cool(self) -> None:
        """ A new ship """
        self.heat = 0.
