""" Ore lost in a crash, thrown out of the ship in canisters, which turn
with the asteroids around them or settle on an orbit around a planet """

import math
from dataclasses import dataclass
from random import Random

from ..world.space import Celestial, Vec2
from .config import (
    CANISTER_DRAG,
    CANISTER_GATHER,
    CANISTER_GATHER_SPEED,
    CANISTER_ORBIT_ALTITUDE,
    CANISTER_ORBIT_DRAG,
    CANISTER_SPEED,
    CANISTER_SPIN,
    CANISTER_SPREAD,
    CANISTER_UNITS,
)
from .ore import EPSILON, Hold


@dataclass(frozen=True)
class CanisterPlan:
    mineral: str
    amount: float
    pos: Vec2
    velocity: Vec2
    angle: float
    spin: float               # radians/s
    altitude: float           # of its orbit, around a planet


def canister_texture(mineral: str) -> str:
    return f'canister_{mineral}'


def eject_cargo(rng: Random, ore: Hold, pos: Vec2,
                velocity: Vec2, away: float) -> list[CanisterPlan]:
    """ The ore split in canisters of CANISTER_UNITS at most, thrown from
    `pos` in a fan around the direction `away`, along with `velocity` """
    plans = []
    for mineral, amount in ore.items():
        if amount <= EPSILON:
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
                altitude=rng.uniform(*CANISTER_ORBIT_ALTITUDE),
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


def orbit_flow(pos: Vec2, body: Celestial, altitude: float,
               dt: float) -> Vec2:
    """ Velocity turning around `body`, at the speed its pull allows, and
    closing in on the orbit at `altitude` above its surface. All turn the
    same way: canisters are deadly, and would cross head-on otherwise. """
    dx, dy = pos[0] - body.pos[0], pos[1] - body.pos[1]
    distance = math.hypot(dx, dy)
    angular_speed = math.sqrt(math.hypot(*body.pull(*pos)) / distance)
    flow_x, flow_y = flow_velocity(
        pos, body.pos, body.velocity, angular_speed, dt,
    )
    away = (body.radius + altitude - distance) * CANISTER_GATHER
    limit = CANISTER_GATHER_SPEED
    gather = max(-limit, min(limit, away)) / distance
    return flow_x + dx * gather, flow_y + dy * gather


def drift(velocity: Vec2, flow: Vec2, dt: float,
          drag: float = CANISTER_DRAG) -> Vec2:
    """ The velocity relative to the flow fades away """
    keep = math.exp(-drag * dt)
    return (
        flow[0] + (velocity[0] - flow[0]) * keep,
        flow[1] + (velocity[1] - flow[1]) * keep,
    )


def settle(pos: Vec2, velocity: Vec2, body: Celestial, altitude: float,
           dt: float) -> Vec2:
    """ Turning around `body` as fast as the canister goes, not to fly off
    or fall in while it picks up speed, what departs from the orbit fading
    away """
    dx, dy = pos[0] - body.pos[0], pos[1] - body.pos[1]
    vx, vy = velocity[0] - body.velocity[0], velocity[1] - body.velocity[1]
    square = dx * dx + dy * dy
    turn = ((dx * vy - dy * vx) / square) ** 2 * dt
    return drift(
        (velocity[0] - dx * turn, velocity[1] - dy * turn),
        orbit_flow(pos, body, altitude, dt), dt, CANISTER_ORBIT_DRAG,
    )
