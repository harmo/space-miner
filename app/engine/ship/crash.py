""" The ship touching something: a crash, unless it lands softly on the
Earth """

import math
from dataclasses import dataclass
from typing import Any

from ...logic.ship.ship import Ship, is_crash
from ...logic.world.space import Vec2
from ..entities import GameWorld, get_body


@dataclass(frozen=True)
class Crash:
    velocity: Vec2            # of what the ship crashed in
    away: float               # direction from it to the ship


def crash_of(gameworld: GameWorld, ship: Ship, arbiter: Any,
             earth_id: int) -> Crash | None:
    """ From the contact the physics engine reports """
    first, second = (shape.body.data for shape in arbiter.shapes)
    other = second if first == ship.entity_id else first
    body = get_body(gameworld, other)
    velocity, position = body.velocity, body.position
    relative_speed = math.hypot(
        ship.velocity[0] - velocity.x, ship.velocity[1] - velocity.y,
    )
    if not is_crash(relative_speed, other == earth_id):
        return None
    x, y = ship.position
    return Crash(
        (velocity.x, velocity.y),
        math.atan2(y - position.y, x - position.x),
    )
