""" Landing legs: folded along the rear of the ship in flight, unfolded
backwards and outwards to stand on the ground, which they never go into """

import math

from ..world.space import Round, Vec2
from .config import LEG_DEPLOY_TIME, LEG_LENGTH, LEG_SPREAD

Leg = tuple[Vec2, Vec2]       # hip on the hull, foot


def to_world(pos: Vec2, angle: float, local: Vec2) -> Vec2:
    """ From the frame of the ship, its nose along +x """
    cos, sin = math.cos(angle), math.sin(angle)
    x, y = local
    return pos[0] + x * cos - y * sin, pos[1] + x * sin + y * cos


def ground_hit(hip: Vec2, foot: Vec2, ground: Round) -> Vec2:
    """ Where the leg from `hip` to `foot` meets the ground, the foot when
    it doesn't """
    cx, cy = ground.pos
    if math.dist(foot, (cx, cy)) >= ground.radius:
        return foot
    # |hip + t * (foot - hip) - center| = radius, smallest t in [0, 1]
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    fx, fy = hip[0] - cx, hip[1] - cy
    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - ground.radius ** 2
    if c <= 0 or a == 0:
        return hip                    # the hip itself is in the ground
    t = (-b - math.sqrt(max(0., b * b - 4 * a * c))) / (2 * a)
    t = min(1., max(0., t))
    return hip[0] + dx * t, hip[1] + dy * t


def legs(
    pos: Vec2,
    angle: float,
    size: Vec2,
    unfolded: float,
    ground: Round
) -> list[Leg]:
    """ Both legs of a ship of `size`, unfolded from 0 to 1 """
    length, width = size
    hip_x = -length / 2 + 3.
    folded_x = -length / 2
    legs = []
    for side in (1, -1):
        hip = (hip_x, side * width * .3)
        folded = (folded_x, side * width * .4)
        spread = (-length / 2 - LEG_LENGTH, side * (width / 2 + LEG_SPREAD))
        foot = (
            folded[0] + (spread[0] - folded[0]) * unfolded,
            folded[1] + (spread[1] - folded[1]) * unfolded,
        )
        world_hip = to_world(pos, angle, hip)
        world_foot = to_world(pos, angle, foot)
        legs.append((world_hip, ground_hit(world_hip, world_foot, ground)))
    return legs


def unfold(unfolded: float, dt: float, out: bool) -> float:
    """ Moves towards unfolded, or folded """
    step = dt / LEG_DEPLOY_TIME
    if out:
        return min(1., unfolded + step)
    return max(0., unfolded - step)
