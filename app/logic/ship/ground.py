""" The ground of bodies, the Earth or an outpost: where ships fit on it,
and how they stand there """

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from ..world.space import Celestial, Vec2, angle_diff
from .config import (
    GROUND_SAFETY,
    LANDED_GAP,
    LANDED_SPEED,
    LEG_LENGTH,
)
from .pose import Pose, ShipSize

# What ships land on: land, the pad of an outpost, the port of a station
GroundKind = Literal['land', 'pad', 'port']


def landed_distance(body: Celestial, length: float) -> float:
    """ From the body center to a ship of this length landed with its
    nose up, standing on its legs """
    return body.radius + length / 2 + LEG_LENGTH


def landed_on(body: Celestial, direction: float, length: float) -> Vec2:
    """ Position of the ship landed on a body, in `direction` from its
    center, with its nose pointing the same way """
    x, y = body.pos
    distance = landed_distance(body, length)
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


def pad_edge(radius: float, direction: float,
             width: float) -> tuple[bool, ...]:
    """ The ground of an outpost: a pad `width` wide, in `direction` from
    the center of a body of `radius` """
    half = math.degrees(width / 2 / radius)
    middle = math.degrees(direction)
    return tuple(
        abs((degree - middle + 180) % 360 - 180) <= half
        for degree in range(360)
    )


def ground_margin(body: Celestial, width: float) -> int:
    """ Degrees of ground needed on each side of the ship center """
    return (
        math.ceil(math.degrees(width / 2 / body.radius))
        + GROUND_SAFETY
    )


def ground_spots(edge: Sequence[bool], margin: int) -> list[float]:
    """ Directions where the ship fits on the ground. `edge` holds one
    sample per degree, counterclockwise from the east, and the ship needs
    `margin` degrees of ground on each side. """
    count = len(edge)
    return [
        math.radians(index * 360 / count)
        for index in range(count)
        if all(
            edge[(index + offset) % count]
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


def surface_distance(pos: Vec2, body: Celestial) -> float:
    return math.dist(pos, body.pos) - body.radius


def ground_gap(pos: Vec2, angle: float, body: Celestial,
               size: ShipSize) -> float:
    """ Between the ground and the ship, a box of `size` turned by
    `angle`: it lies closer to the ground on its side than on its nose """
    x, y = body.pos
    tilt = angle - math.atan2(pos[1] - y, pos[0] - x)
    reach = (
        abs(math.cos(tilt)) * size.length / 2
        + abs(math.sin(tilt)) * size.width / 2
    )
    return surface_distance(pos, body) - reach


def is_landed(pose: Pose, body: Celestial, size: ShipSize) -> bool:
    """ Touching the ground, or standing on its legs, at the speed of the
    body """
    vx, vy = body.velocity
    ship_vx, ship_vy = pose.velocity
    return (
        ground_gap(pose.position, pose.angle, body, size)
        < LEG_LENGTH + LANDED_GAP
        and math.hypot(ship_vx - vx, ship_vy - vy) < LANDED_SPEED
    )


class Grounds:
    """ Where ships can land, the first one their home where they come
    back after a crash, and where the ship fits on each """

    def __init__(self, grounds: Sequence[Ground]) -> None:
        self.grounds = tuple(grounds)
        self.fits: dict[int, list[float]] = {}  # spots, by body

    @property
    def home(self) -> Ground:
        return self.grounds[0]

    @property
    def landable(self) -> set[int]:
        """ Entities ships can land on rather than crash """
        return {ground.body.entity_id for ground in self.grounds}

    def fit(self, width: float) -> None:
        """ For a ship of `width` """
        self.fits = {
            ground.body.entity_id: ground.spots(width)
            for ground in self.grounds
        }

    def spots(self, ground: Ground) -> list[float]:
        return self.fits[ground.body.entity_id]

    def nearest(self, pos: Vec2) -> Ground:
        """ The closest to `pos` """
        return min(
            self.grounds,
            key=lambda ground: surface_distance(pos, ground.body),
        )

    def of(self, body: Celestial) -> Ground | None:
        return next(
            (ground for ground in self.grounds if ground.body is body), None,
        )
