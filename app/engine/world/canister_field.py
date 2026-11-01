""" Canisters floating in space, as KivEnt entities """

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from ...logic.mining.canisters import (
    CanisterPlan,
    drift,
    flow_velocity,
    settle,
)
from ...logic.mining.config import (
    CANISTER_FOLLOW_RANGE,
    CANISTER_MAX,
    CANISTER_NEIGHBOR_PERIOD,
    CANISTER_SIZE,
    CANISTER_SUN_ALTITUDE,
    CANISTER_SUN_REACH,
)
from ...logic.world.space import (
    Celestial,
    Orbit,
    Vec2,
    closest_pulling,
    closest_to,
    nearest,
    strongest,
    wrap_shift,
)
from ...logic.world.state import LostCanister
from ..entities import GameWorld, create_canister_entity, get_body, move_body


@dataclass(eq=False)
class Canister:
    mineral: str
    amount: float
    entity_id: int
    body: Any                 # cymunk Body
    altitude: float           # of its orbit, around a planet
    # Asteroid it turns with, looked for again from time to time
    neighbor: Celestial | None = field(default=None, repr=False)

    @property
    def pos(self) -> Vec2:
        return self.body.position.x, self.body.position.y

    @property
    def velocity(self) -> Vec2:
        return self.body.velocity.x, self.body.velocity.y

    @property
    def orbit(self) -> Orbit | None:
        return None

    @property
    def radius(self) -> float:
        return CANISTER_SIZE[0] / 2


class CanisterField:

    def __init__(self, gameworld: GameWorld) -> None:
        self.gameworld = gameworld
        self.canisters: list[Canister] = []
        self.neighbors_in = 0.

    def add(self, plans: Iterable[CanisterPlan]) -> None:
        for plan in plans:
            entity_id = create_canister_entity(self.gameworld, plan)
            self.canisters.append(Canister(
                plan.mineral, plan.amount, entity_id,
                get_body(self.gameworld, entity_id), plan.altitude,
            ))
        while len(self.canisters) > CANISTER_MAX:
            self.remove(self.canisters[0])

    def lost(self, attractors: Sequence[Celestial]) -> list[LostCanister]:
        """ To save: each from what it floats around """
        states = []
        for canister in self.canisters:
            pos = canister.pos
            body = closest_pulling(pos, attractors) or attractors[0]
            states.append(LostCanister(
                canister.mineral, canister.amount, canister.altitude,
                attractors.index(body),
                (pos[0] - body.pos[0], pos[1] - body.pos[1]),
            ))
        return states

    def recover(
        self,
        lost: Iterable[LostCanister],
        attractors: Sequence[Celestial]
    ) -> None:
        """ Around the same bodies, moving along with them """
        plans = []
        for canister in lost:
            body = attractors[min(canister.around, len(attractors) - 1)]
            plans.append(CanisterPlan(
                canister.mineral, canister.amount,
                (body.pos[0] + canister.offset[0],
                 body.pos[1] + canister.offset[1]),
                body.velocity, 0., 0., canister.altitude,
            ))
        self.add(plans)

    def remove(self, canister: Canister) -> None:
        self.canisters.remove(canister)
        self.gameworld.remove_entity(canister.entity_id)

    def at(self, pos: Vec2, tolerance: float) -> Canister | None:
        return closest_to(pos, self.canisters, tolerance)

    def update(
        self,
        dt: float,
        asteroids: Sequence[Celestial],
        attractors: Sequence[Celestial]
    ) -> None:
        """ Canisters gather on an orbit around the closest planet in
        reach, or around the sun inside the orbit of the first planet.
        Elsewhere, they slow down relative to the asteroids around them
        and turn with them, or stop along with the sun. """
        self.neighbors_in -= dt
        if self.neighbors_in <= 0:
            self.neighbors_in = CANISTER_NEIGHBOR_PERIOD
            for canister in self.canisters:
                canister.neighbor = nearest(
                    canister.pos, asteroids, CANISTER_FOLLOW_RANGE
                )
        alive = set(asteroids)

        for canister in self.canisters:
            pos, velocity = canister.pos, canister.velocity
            planet = closest_pulling(pos, attractors)
            sun = attractors[0]
            neighbor = canister.neighbor
            orbit = neighbor.orbit if neighbor in alive and neighbor else None
            if planet is not None:
                canister.body.velocity = settle(
                    pos, velocity, planet, canister.altitude, dt,
                )
            elif math.dist(pos, sun.pos) - sun.radius < CANISTER_SUN_REACH:
                canister.body.velocity = settle(
                    pos, velocity, sun,
                    CANISTER_SUN_ALTITUDE + canister.altitude, dt,
                )
            elif orbit is not None:
                parent = orbit.parent
                canister.body.velocity = drift(velocity, flow_velocity(
                    pos, parent.pos, parent.velocity, orbit.angular_speed, dt,
                ), dt)
            else:
                attractor = strongest(pos, attractors)
                flow = attractor.velocity if attractor else (0., 0.)
                canister.body.velocity = drift(velocity, flow, dt)

    def shift(self, shift: Vec2) -> None:
        for canister in self.canisters:
            move_body(self.gameworld, canister.entity_id, shift)

    def wrap(self, center: Vec2) -> None:
        """ Move canisters to their copy closest to center """
        for canister in self.canisters:
            shift = wrap_shift(canister.pos, center)
            if shift != (0, 0):
                move_body(self.gameworld, canister.entity_id, shift)
