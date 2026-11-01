""" Mechanics of space: repetition, orbits, gravity, and finding what is
around """

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Generic, Protocol, TypeVar

from ..config import WORLD_SIZE
from .config import GRAVITY_FALLOFF, GRAVITY_RANGE

Vec2 = tuple[float, float]


def wrap_shift(pos: Vec2, center: Vec2, period: float = WORLD_SIZE) -> Vec2:
    """ Offset moving pos to its copy closest to center in periodic space """
    return (
        period * round((center[0] - pos[0]) / period),
        period * round((center[1] - pos[1]) / period),
    )


def bearing(pos: Vec2, center: Vec2) -> float:
    """ Direction of `pos`, seen from `center` """
    return math.atan2(pos[1] - center[1], pos[0] - center[0])


def angle_diff(a: float, b: float) -> float:
    """ Shortest turn from b to a, between -pi and pi """
    return (a - b + math.pi) % (2 * math.pi) - math.pi


class Orbit:
    """ Circular orbit around a parent celestial body """

    def __init__(
        self,
        parent: Celestial,
        radius: float,
        speed: float,
        angle: float
    ) -> None:
        self.parent = parent
        self.radius = radius
        self.angular_speed = speed / radius
        self.angle = angle

    def advance(self, dt: float) -> None:
        self.angle += self.angular_speed * dt

    @property
    def position(self) -> Vec2:
        x, y = self.parent.pos
        return (
            x + self.radius * math.cos(self.angle),
            y + self.radius * math.sin(self.angle),
        )

    @property
    def velocity(self) -> Vec2:
        """ Includes the parent's velocity, so satellites keep up with it """
        vx, vy = self.parent.velocity
        tangent_speed = self.angular_speed * self.radius
        return (
            vx - math.sin(self.angle) * tangent_speed,
            vy + math.cos(self.angle) * tangent_speed,
        )


class Round(Protocol):
    """ Something round, under a click or a circle """

    @property
    def pos(self) -> Vec2: ...

    @property
    def radius(self) -> float: ...


R = TypeVar('R', bound=Round)


def closest_to(
    pos: Vec2,
    things: Iterable[R],
    tolerance: float
) -> R | None:
    """ Closest thing whose edge is within tolerance of pos """
    closest, closest_gap = None, tolerance
    for thing in things:
        gap = math.dist(pos, thing.pos) - thing.radius
        if gap <= closest_gap:
            closest, closest_gap = thing, gap
    return closest


class Target(Protocol):
    """ Something moving that a ship can hold next to """

    @property
    def pos(self) -> Vec2: ...

    @property
    def velocity(self) -> Vec2: ...

    @property
    def orbit(self) -> Orbit | None: ...


# A station of a planet is a station of something moving
T_co = TypeVar('T_co', bound=Target, covariant=True)


class Station(Generic[T_co]):
    """ Spot at a fixed distance from a target, which keeps its place
    relative to the orbit of the target: a ship holding there flies in
    formation with it """

    def __init__(
        self,
        target: T_co,
        start: Vec2,
        distance: float
    ) -> None:
        self.target = target
        self.distance = distance
        self.angle = bearing(start, target.pos) - self.orbit_angle

    @property
    def orbit_angle(self) -> float:
        orbit = self.target.orbit
        return orbit.angle if orbit else 0.

    @property
    def position(self) -> Vec2:
        angle = self.orbit_angle + self.angle
        x, y = self.target.pos
        return (
            x + math.cos(angle) * self.distance,
            y + math.sin(angle) * self.distance,
        )

    @property
    def velocity(self) -> Vec2:
        """ The velocity of the target, plus turning along with its orbit """
        orbit = self.target.orbit
        tangent_speed = self.distance * (orbit.angular_speed if orbit else 0.)
        angle = self.orbit_angle + self.angle
        vx, vy = self.target.velocity
        return (
            vx - math.sin(angle) * tangent_speed,
            vy + math.cos(angle) * tangent_speed,
        )


class Celestial:
    """ The sun, a planet, the moon or an asteroid. Bodies on an orbit derive
    their position from it, so moving the sun moves the whole system. """

    def __init__(
        self,
        entity_id: int,
        radius: float,
        *,
        pos: Vec2 = (0., 0.),
        orbit: Orbit | None = None,
        gravity: float = 0.,
        gravity_falloff: float = GRAVITY_FALLOFF,
        gravity_range: float | None = GRAVITY_RANGE,
        mineral: str | None = None
    ) -> None:
        self.entity_id = entity_id
        self.radius = radius
        self._pos = pos               # only used when not on an orbit
        self.orbit = orbit
        self.gravity = gravity        # pull at the surface (px/s²)
        self.gravity_falloff = gravity_falloff
        self.gravity_range = gravity_range  # in radii, None for no limit
        self.mineral = mineral              # for asteroids

    @property
    def pos(self) -> Vec2:
        return self.orbit.position if self.orbit else self._pos

    @property
    def velocity(self) -> Vec2:
        return self.orbit.velocity if self.orbit else (0., 0.)

    def shift(self, shift: Vec2) -> None:
        self._pos = (self._pos[0] + shift[0], self._pos[1] + shift[1])

    def pull(self, x: float, y: float) -> Vec2:
        """ Acceleration on a ship at (x, y): gravity at the surface, then
        fading as (radius / distance) ** falloff, none when out of range """
        dx = self.pos[0] - x
        dy = self.pos[1] - y
        distance = math.hypot(dx, dy)
        if not self.gravity or (
            self.gravity_range is not None
            and distance > self.radius * self.gravity_range
        ):
            return 0., 0.
        pull = self.gravity * (
            self.radius / max(distance, self.radius)
        ) ** self.gravity_falloff
        return dx / distance * pull, dy / distance * pull


def nearest(
    pos: Vec2,
    bodies: Iterable[Celestial],
    within: float
) -> Celestial | None:
    """ Closest body whose center is within the distance `within` """
    closest, closest_distance = None, within
    for body in bodies:
        distance = math.dist(pos, body.pos)
        if distance <= closest_distance:
            closest, closest_distance = body, distance
    return closest


def closest_pulling(
    pos: Vec2,
    attractors: Sequence[Celestial]
) -> Celestial | None:
    """ The closest body on an orbit whose gravity reaches pos: the sun is
    not one """
    pulling = [
        body for body in attractors
        if body.orbit is not None and any(body.pull(*pos))
    ]
    return min(
        pulling, key=lambda body: math.dist(pos, body.pos), default=None,
    )


def strongest(pos: Vec2, attractors: Sequence[Celestial]) -> Celestial | None:
    """ The body pulling the most at pos """
    best, best_pull = None, 0.
    for attractor in attractors:
        pull = math.hypot(*attractor.pull(*pos))
        if pull > best_pull:
            best, best_pull = attractor, pull
    return best
