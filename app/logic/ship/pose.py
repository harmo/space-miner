""" Where a ship stands, how it moves, and how large it is """

from dataclasses import dataclass
from typing import NamedTuple

from ..world.space import Vec2


@dataclass(frozen=True)
class Pose:
    position: Vec2
    velocity: Vec2
    angle: float


class ShipSize(NamedTuple):
    length: float
    width: float
