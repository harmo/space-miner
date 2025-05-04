""" Ore lost in a crash, thrown out of the ship in canisters """

import math
from dataclasses import dataclass
from random import Random

from ..world.space import Vec2
from .config import (
    CANISTER_DRAG,
    CANISTER_SPEED,
    CANISTER_SPIN,
    CANISTER_SPREAD,
    CANISTER_UNITS,
)


@dataclass(frozen=True)
class CanisterPlan:
    mineral: str
    amount: float
    pos: Vec2
    velocity: Vec2
    angle: float
    spin: float               # radians/s


def canister_texture(mineral: str) -> str:
    return f'canister_{mineral}'


def eject_cargo(rng: Random, ore: dict[str, float], pos: Vec2,
                velocity: Vec2, away: float) -> list[CanisterPlan]:
    """ The ore split in canisters of CANISTER_UNITS at most, thrown from
    `pos` in a fan around the direction `away`, along with `velocity` """
    plans = []
    for mineral, amount in ore.items():
        if amount <= 1e-6:
            continue
        count = math.ceil(amount / CANISTER_UNITS - 1e-9)
        for _ in range(count):
            direction = away + math.radians(
                rng.uniform(-CANISTER_SPREAD, CANISTER_SPREAD)
            )
            speed = rng.uniform(*CANISTER_SPEED)
            plans.append(CanisterPlan(
                mineral, amount / count, pos,
                (
                    velocity[0] + math.cos(direction) * speed,
                    velocity[1] + math.sin(direction) * speed,
                ),
                angle=rng.uniform(0, 2 * math.pi),
                spin=math.radians(rng.uniform(-CANISTER_SPIN, CANISTER_SPIN)),
            ))
    return plans


def flow_velocity(pos: Vec2, center: Vec2, center_velocity: Vec2,
                  angular_speed: float, dt: float) -> Vec2:
    """ Velocity turning pos around a center moving at center_velocity, as
    an orbit at angular_speed does. Computed from the exact rotation over
    dt, so that it stays on its circle. """
    dx, dy = pos[0] - center[0], pos[1] - center[1]
    cos, sin = math.cos(angular_speed * dt), math.sin(angular_speed * dt)
    return (
        center_velocity[0] + (dx * cos - dy * sin - dx) / dt,
        center_velocity[1] + (dx * sin + dy * cos - dy) / dt,
    )


def drift(velocity: Vec2, flow: Vec2, dt: float) -> Vec2:
    """ The velocity relative to the flow fades away """
    keep = math.exp(-CANISTER_DRAG * dt)
    return (
        flow[0] + (velocity[0] - flow[0]) * keep,
        flow[1] + (velocity[1] - flow[1]) * keep,
    )
