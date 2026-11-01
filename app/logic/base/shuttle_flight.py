""" How shuttles fly: straight to where they go, rounding whatever stands
in the way, on the side where it lies """

import math
from collections.abc import Sequence
from dataclasses import dataclass

from ..world.space import Vec2
from .config import SHUTTLE_TURN

AWARE = 30.                   # pixels: rounding starts this close


@dataclass(frozen=True)
class Obstacle:
    pos: Vec2
    reach: float              # from its center, shuttles stay out of it


@dataclass(frozen=True)
class Airspace:
    """ Where shuttles fly, as it is now """
    sun: Vec2                 # what shuttles keep their place from
    obstacles: Sequence[Obstacle]


def crosses(start: Vec2, end: Vec2, obstacle: Obstacle) -> bool:
    """ The way from `start` to `end` goes through it. Never when leaving
    it, even from its edge, where it pushes what it moves against. """
    x, y = start
    dx, dy = end[0] - x, end[1] - y
    squared = dx * dx + dy * dy
    cx, cy = obstacle.pos
    along = ((cx - x) * dx + (cy - y) * dy) / squared if squared else 0.
    if along <= 0:
        return False
    along = min(along, 1.)
    closest = (x + dx * along, y + dy * along)
    return math.dist(closest, obstacle.pos) < obstacle.reach


def direction(
    pos: Vec2,
    goal: Vec2,
    obstacles: Sequence[Obstacle]
) -> float:
    """ To the goal, or around the closest obstacle in the way """
    wanted = math.atan2(goal[1] - pos[1], goal[0] - pos[0])
    blocking = [
        obstacle for obstacle in obstacles
        if math.dist(pos, obstacle.pos) < obstacle.reach + AWARE
        and crosses(pos, goal, obstacle)
    ]
    if not blocking:
        return wanted
    closest = min(blocking, key=lambda o: math.dist(pos, o.pos))
    away = math.atan2(pos[1] - closest.pos[1], pos[0] - closest.pos[0])
    turn = math.remainder(wanted - away, math.tau)
    return away + math.copysign(math.pi / 2, turn)


def kept_out(pos: Vec2, obstacles: Sequence[Obstacle]) -> Vec2:
    """ Bodies move too: pushed out of those coming upon it """
    for obstacle in obstacles:
        cx, cy = obstacle.pos
        distance = math.dist(pos, obstacle.pos)
        if 0 < distance < obstacle.reach:
            scale = obstacle.reach / distance
            pos = (cx + (pos[0] - cx) * scale, cy + (pos[1] - cy) * scale)
    return pos


def fly(
    pos: Vec2,
    goal: Vec2,
    obstacles: Sequence[Obstacle],
    step: float
) -> tuple[Vec2, float]:
    """ `step` pixels on: where it gets to, and the way it went """
    angle = direction(pos, goal, obstacles)
    moved = (pos[0] + math.cos(angle) * step, pos[1] + math.sin(angle) * step)
    return kept_out(moved, obstacles), angle


def turned(heading: float, wanted: float, dt: float) -> float:
    """ Its nose follows, not to shake when rounding a body """
    turn = math.remainder(wanted - heading, math.tau)
    most = SHUTTLE_TURN * dt
    return heading + max(-most, min(turn, most))
