""" Landing on the ground of a body, the Earth or an outpost, automatically
through a shortcut shown nearby """

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from ..world.space import Celestial, Vec2, angle_diff
from .config import (
    GROUND_SAFETY,
    LANDED_GAP,
    LANDED_SPEED,
    LANDING_DURATION,
    LANDING_RANGE,
    LEG_LENGTH,
    SHORTCUT_RANGE,
)

# Hidden, shown but too far to be used, close enough but not above where
# the ship can land,
# or ready to be used
Shortcut = Literal['hidden', 'far', 'aside', 'ready']
# What ships land on: land, the pad of an outpost, the port of a station
GroundKind = Literal['land', 'pad', 'port']
# Told beside it
ASIDE: dict[GroundKind, str] = {
    'land': "Au-dessus de l'eau",
    'pad': 'Hors de la plateforme',
    'port': 'Hors du port',
}


def landed_distance(planet: Celestial, length: float) -> float:
    """ From the planet center to a ship of this length landed with its
    nose up, standing on its legs """
    return planet.radius + length / 2 + LEG_LENGTH


def landed_on(planet: Celestial, direction: float, length: float) -> Vec2:
    """ Position of the ship landed on a planet, in `direction` from its
    center, with its nose pointing the same way """
    x, y = planet.pos
    distance = landed_distance(planet, length)
    return (
        x + math.cos(direction) * distance,
        y + math.sin(direction) * distance,
    )


@dataclass(frozen=True)
class Ground:
    """ A body ships can land on, and where: one sample per degree,
    counterclockwise from the east, true over solid ground """
    body: Celestial
    edge: tuple[bool, ...]
    kind: GroundKind = 'land'

    def spots(self, width: float) -> list[float]:
        """ Directions where a ship of `width` fits """
        return ground_spots(self.edge, ground_margin(self.body, width))


def pad(radius: float, direction: float, width: float) -> tuple[bool, ...]:
    """ The ground of an outpost: a pad `width` wide, in `direction` from
    the center of a body of `radius` """
    half = math.degrees(width / 2 / radius)
    middle = math.degrees(direction)
    return tuple(
        abs((degree - middle + 180) % 360 - 180) <= half
        for degree in range(360)
    )


def nearest(grounds: Sequence[Ground], pos: Vec2) -> Ground:
    """ Of the grounds, the closest to `pos` """
    return min(
        grounds, key=lambda ground: surface_distance(pos, ground.body)
    )


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


def parking_on(planet: Celestial, direction: float,
               length: float) -> Parking:
    """ Landed in `direction`, with the nose pointing the same way """
    return Parking(
        planet, direction, landed_distance(planet, length), direction,
    )


def parking_at(planet: Celestial, pos: Vec2, angle: float) -> Parking:
    """ Landed where the ship is, as it is """
    x, y = planet.pos
    return Parking(
        planet, math.atan2(pos[1] - y, pos[0] - x), math.dist(pos, (x, y)),
        angle,
    )


def ground_margin(planet: Celestial, width: float) -> int:
    """ Degrees of ground needed on each side of the ship center """
    return (
        math.ceil(math.degrees(width / 2 / planet.radius))
        + GROUND_SAFETY
    )


def ground_spots(ground: Sequence[bool], margin: int) -> list[float]:
    """ Directions where the ship fits on the ground. `ground` holds one
    sample per degree, counterclockwise from the east, and the ship needs
    `margin` degrees of ground on each side. """
    count = len(ground)
    return [
        math.radians(index * 360 / count)
        for index in range(count)
        if all(
            ground[(index + offset) % count]
            for offset in range(-margin, margin + 1)
        )
    ]


def closest_spot(direction: float, spots: Sequence[float]) -> float:
    """ The spot closest to `direction`, or `direction` without any """
    if not spots:
        return direction
    return min(spots, key=lambda spot: abs(angle_diff(spot, direction)))


def over_ground(direction: float, spots: Sequence[float]) -> bool:
    """ Whether a spot lies right below `direction`, spots being a degree
    apart """
    if not spots:
        return False
    spot = closest_spot(direction, spots)
    return abs(angle_diff(spot, direction)) <= math.radians(.5) + 1e-9


def surface_distance(pos: Vec2, planet: Celestial) -> float:
    return math.dist(pos, planet.pos) - planet.radius


def ground_gap(pos: Vec2, angle: float, planet: Celestial,
               size: Vec2) -> float:
    """ Between the ground and the ship, a box of `size` turned by
    `angle`: it lies closer to the ground on its side than on its nose """
    x, y = planet.pos
    length, width = size
    tilt = angle - math.atan2(pos[1] - y, pos[0] - x)
    reach = (
        abs(math.cos(tilt)) * length / 2 + abs(math.sin(tilt)) * width / 2
    )
    return surface_distance(pos, planet) - reach


def is_landed(pos: Vec2, velocity: Vec2, angle: float,
              planet: Celestial, size: Vec2) -> bool:
    """ Touching the ground, or standing on its legs, at the speed of the
    planet """
    vx, vy = planet.velocity
    return (
        ground_gap(pos, angle, planet, size) < LEG_LENGTH + LANDED_GAP
        and math.hypot(velocity[0] - vx, velocity[1] - vy) < LANDED_SPEED
    )


def shortcut(distance: float, landed: bool, ground: bool) -> Shortcut:
    """ State of the shortcut at `distance` from the surface, above the
    `ground` or aside from it """
    if landed or distance > SHORTCUT_RANGE:
        return 'hidden'
    if distance > LANDING_RANGE:
        return 'far'
    return 'ready' if ground else 'aside'


def shortcut_text(state: Shortcut, kind: GroundKind) -> str:
    """ Shown on the shortcut, near that kind of ground """
    if state == 'aside':
        return ASIDE[kind]
    return "S'amarrer" if kind == 'port' else 'Atterrir'


def ease(progress: float) -> float:
    """ Smooth from 0 to 1: starts and ends without speed """
    return progress * progress * (3 - 2 * progress)


def ease_slope(progress: float) -> float:
    return 6 * progress * (1 - progress)


class Landing:
    """ The ship turns its nose away from the planet and comes down to the
    spot in `end_direction`, going around the planet if needed, where it
    arrives without speed. Computed relative to the planet, which keeps
    moving meanwhile. """

    def __init__(self, planet: Celestial, start: Vec2, start_angle: float,
                 end_direction: float, length: float,
                 duration: float = LANDING_DURATION) -> None:
        self.planet = planet
        x, y = planet.pos
        self.start_direction = math.atan2(start[1] - y, start[0] - x)
        self.end_direction = end_direction
        self.around = angle_diff(end_direction, self.start_direction)
        self.start_distance = math.dist(start, (x, y))
        self.end_distance = landed_distance(planet, length)
        self.start_angle = start_angle
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
        """ Of the ship, seen from the planet center """
        return self.start_direction + self.around * ease(self.progress)

    @property
    def distance(self) -> float:
        """ From the planet center """
        return self.start_distance + (
            self.end_distance - self.start_distance
        ) * ease(self.progress)

    @property
    def position(self) -> Vec2:
        x, y = self.planet.pos
        return (
            x + math.cos(self.direction) * self.distance,
            y + math.sin(self.direction) * self.distance,
        )

    @property
    def velocity(self) -> Vec2:
        vx, vy = self.planet.velocity
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
