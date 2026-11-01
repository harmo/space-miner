""" Ships staying on the ground of a body """

import math
from dataclasses import dataclass

from ..world.space import Celestial, Vec2, bearing
from .ground import landed_distance
from .pose import Pose


@dataclass(frozen=True)
class Parking:
    """ Where a landed ship stays on a body, moving along with it, as
    physics alone would let it slide: the pull of the sun drags it aside """
    body: Celestial
    direction: float          # from the body center
    distance: float           # from the body center
    angle: float              # of the ship

    @property
    def position(self) -> Vec2:
        x, y = self.body.pos
        return (
            x + math.cos(self.direction) * self.distance,
            y + math.sin(self.direction) * self.distance,
        )

    @property
    def pose(self) -> Pose:
        return Pose(self.position, self.body.velocity, self.angle)


def parking_on(
    body: Celestial,
    direction: float,
    length: float
) -> Parking:
    """ Landed in `direction`, with the nose pointing the same way """
    return Parking(
        body, direction, landed_distance(body, length), direction,
    )


def parking_at(body: Celestial, pose: Pose) -> Parking:
    """ Landed where the ship is, as it is """
    return Parking(
        body, bearing(pose.position, body.pos),
        math.dist(pose.position, body.pos), pose.angle,
    )
