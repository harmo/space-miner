""" Landing on the ground of a body, automatically through the shortcut """

import math

from ..world.space import Celestial, Vec2, angle_diff
from .config import LANDING_DURATION
from .ground import landed_distance
from .pose import Pose


def ease(progress: float) -> float:
    """ Smooth from 0 to 1: starts and ends without speed """
    return progress * progress * (3 - 2 * progress)


def ease_slope(progress: float) -> float:
    return 6 * progress * (1 - progress)


class Landing:
    """ The ship turns its nose away from the body and comes down to the
    spot in `end_direction`, going around the body if needed, where it
    arrives without speed. Computed relative to the body, which keeps
    moving meanwhile. """

    def __init__(self, body: Celestial, start: Pose,
                 end_direction: float, length: float,
                 duration: float = LANDING_DURATION) -> None:
        self.body = body
        x, y = body.pos
        start_x, start_y = start.position
        self.start_direction = math.atan2(start_y - y, start_x - x)
        self.end_direction = end_direction
        self.around = angle_diff(end_direction, self.start_direction)
        self.start_distance = math.dist(start.position, (x, y))
        self.end_distance = landed_distance(body, length)
        self.start_angle = start.angle
        self.duration = duration
        self.age = 0.

    @property
    def progress(self) -> float:
        return min(1., self.age / self.duration)

    @property
    def done(self) -> bool:
        return self.age >= self.duration

    def advance(self, dt: float) -> None:
        self.age += dt

    @property
    def direction(self) -> float:
        """ Of the ship, seen from the body center """
        return self.start_direction + self.around * ease(self.progress)

    @property
    def distance(self) -> float:
        """ From the body center """
        return self.start_distance + (
            self.end_distance - self.start_distance
        ) * ease(self.progress)

    @property
    def position(self) -> Vec2:
        x, y = self.body.pos
        return (
            x + math.cos(self.direction) * self.distance,
            y + math.sin(self.direction) * self.distance,
        )

    @property
    def velocity(self) -> Vec2:
        vx, vy = self.body.velocity
        slope = ease_slope(self.progress) / self.duration
        down = (self.end_distance - self.start_distance) * slope
        around = self.distance * self.around * slope
        cos, sin = math.cos(self.direction), math.sin(self.direction)
        return (
            vx + cos * down - sin * around,
            vy + sin * down + cos * around,
        )

    @property
    def angle(self) -> float:
        """ The nose turns towards space during the first half """
        turn = angle_diff(self.end_direction, self.start_angle)
        return self.start_angle + turn * ease(min(1., 2 * self.progress))

    @property
    def pose(self) -> Pose:
        return Pose(self.position, self.velocity, self.angle)
