""" The player's ship """

import math
from collections.abc import Sequence
from typing import Protocol

from ..world.space import (
    Celestial,
    Station,
    Target,
    Vec2,
    angle_diff,
    strongest,
)
from .config import HOLD_GAIN, HOLD_RESPONSE, LANDING_MAX_SPEED, SHIP_DRAG
from .shipyard import ShipStats


class Vector(Protocol):
    @property
    def x(self) -> float: ...

    @property
    def y(self) -> float: ...


class Body(Protocol):
    """ What the ship needs from its physics body, a cymunk Body in game """
    angle: float
    angular_velocity: float

    @property
    def position(self) -> Vector: ...

    @position.setter
    def position(self, value: Vec2) -> None: ...

    @property
    def velocity(self) -> Vector: ...

    @velocity.setter
    def velocity(self, value: Vec2) -> None: ...


def is_crash(relative_speed: float, landable: bool) -> bool:
    """ Touching anything destroys the ship, except landing softly on a
    body with ground, the Earth or an outpost """
    return not landable or relative_speed > LANDING_MAX_SPEED


class Ship:
    """ Thrusts towards a heading or coasts, or holds in front of a target
    to mine it. Always pulled by the sun and the planets. """

    def __init__(self, entity_id: int, body: Body,
                 stats: ShipStats) -> None:
        self.entity_id = entity_id
        self.body = body
        self.stats = stats

    @property
    def position(self) -> Vec2:
        return self.body.position.x, self.body.position.y

    @property
    def velocity(self) -> Vec2:
        return self.body.velocity.x, self.body.velocity.y

    @property
    def nose(self) -> Vec2:
        x, y = self.position
        half_length = self.stats.size[0] / 2
        return (
            x + math.cos(self.body.angle) * half_length,
            y + math.sin(self.body.angle) * half_length,
        )

    def place(self, position: Vec2, velocity: Vec2, angle: float) -> None:
        """ Move the ship by hand, for animations """
        body = self.body
        body.position = position
        body.velocity = velocity
        body.angle = angle
        body.angular_velocity = 0

    def update(self, dt: float, heading: float | None,
               attractors: Sequence[Celestial]) -> None:
        """ Free flight """
        self.drive(dt, heading, self.reference_velocity(attractors))
        self.apply_gravity(dt, attractors)

    def hold(self, dt: float, station: Station[Target],
             attractors: Sequence[Celestial]) -> None:
        """ Reach and keep the station, facing its target """
        x, y = self.position
        spot_x, spot_y = station.position
        correction_x = (spot_x - x) * HOLD_GAIN
        correction_y = (spot_y - y) * HOLD_GAIN
        correction = math.hypot(correction_x, correction_y)
        max_speed = self.stats.max_speed
        if correction > max_speed:
            correction_x *= max_speed / correction
            correction_y *= max_speed / correction

        # Moving with the station keeps the ship from lagging behind, and the
        # thrusters cancel gravity, or the ship would sag below its spot
        station_vx, station_vy = station.velocity
        gravity_x, gravity_y = self.gravity(attractors)
        target_x, target_y = station.target.pos
        self.turn(dt, math.atan2(target_y - y, target_x - x))
        self.steer(dt, (
            station_vx + correction_x - gravity_x / HOLD_RESPONSE,
            station_vy + correction_y - gravity_y / HOLD_RESPONSE,
        ), HOLD_RESPONSE)
        self.apply_gravity(dt, attractors)

    def reference_velocity(self, attractors: Sequence[Celestial]) -> Vec2:
        """ Velocity of the body pulling the ship the most, the ship thrusts
        and slows down relative to it: landed on a planet, it moves with it """
        attractor = strongest(self.position, attractors)
        return attractor.velocity if attractor else (0., 0.)

    def drive(self, dt: float, heading: float | None,
              reference: Vec2) -> None:
        desired_vx, desired_vy = reference
        rate = SHIP_DRAG
        if heading is not None:
            desired_vx += math.cos(heading) * self.stats.max_speed
            desired_vy += math.sin(heading) * self.stats.max_speed
            rate = self.stats.thrust
            self.turn(dt, heading)
        self.steer(dt, (desired_vx, desired_vy), rate)

    def turn(self, dt: float, heading: float) -> None:
        body = self.body
        delta = angle_diff(heading, body.angle)
        body.angle += delta * min(1., self.stats.turn_speed * dt)

    def steer(self, dt: float, desired: Vec2, rate: float) -> None:
        """ Bring the velocity closer to the desired one """
        body = self.body
        # Turning is driven by the ship, collisions must not make it spin
        body.angular_velocity = 0
        k = min(1., rate * dt)
        body.velocity = (
            body.velocity.x + (desired[0] - body.velocity.x) * k,
            body.velocity.y + (desired[1] - body.velocity.y) * k,
        )

    def gravity(self, attractors: Sequence[Celestial]) -> Vec2:
        ax = ay = 0.
        for attractor in attractors:
            pull_x, pull_y = attractor.pull(*self.position)
            ax += pull_x
            ay += pull_y
        return ax, ay

    def apply_gravity(self, dt: float,
                      attractors: Sequence[Celestial]) -> None:
        ax, ay = self.gravity(attractors)
        self.body.velocity = (
            self.body.velocity.x + ax * dt,
            self.body.velocity.y + ay * dt,
        )
