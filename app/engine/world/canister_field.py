""" Canisters floating in space, as KivEnt entities """

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from ...logic.mining.canisters import CanisterPlan, drift, flow_velocity
from ...logic.mining.config import (
    CANISTER_FOLLOW_RANGE,
    CANISTER_MAX,
    CANISTER_NEIGHBOR_PERIOD,
    CANISTER_SIZE,
)
from ...logic.world.space import (
    Celestial,
    Orbit,
    Vec2,
    closest_to,
    nearest,
    strongest,
    wrap_shift,
)
from ..entities import GameWorld, create_canister_entity, get_body, move_body


@dataclass(eq=False)
class Canister:
    mineral: str
    amount: float
    entity_id: int
    body: Any                 # cymunk Body
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
                get_body(self.gameworld, entity_id),
            ))
        while len(self.canisters) > CANISTER_MAX:
            self.remove(self.canisters[0])

    def remove(self, canister: Canister) -> None:
        self.canisters.remove(canister)
        self.gameworld.remove_entity(canister.entity_id)

    def at(self, pos: Vec2, tolerance: float) -> Canister | None:
        return closest_to(pos, self.canisters, tolerance)

    def update(self, dt: float, asteroids: Sequence[Celestial],
               attractors: Sequence[Celestial]) -> None:
        """ Canisters slow down relative to the asteroids around them, and
        turn with them. Away from asteroids, they move along with what
        pulls them the most. """
        self.neighbors_in -= dt
        if self.neighbors_in <= 0:
            self.neighbors_in = CANISTER_NEIGHBOR_PERIOD
            for canister in self.canisters:
                canister.neighbor = nearest(
                    canister.pos, asteroids, CANISTER_FOLLOW_RANGE
                )
        alive = set(asteroids)

        for canister in self.canisters:
            neighbor = canister.neighbor
            if neighbor is not None and neighbor in alive and neighbor.orbit:
                parent = neighbor.orbit.parent
                flow = flow_velocity(
                    canister.pos, parent.pos, parent.velocity,
                    neighbor.orbit.angular_speed, dt,
                )
            else:
                attractor = strongest(canister.pos, attractors)
                flow = attractor.velocity if attractor else (0., 0.)
            canister.body.velocity = drift(canister.velocity, flow, dt)

    def shift(self, shift: Vec2) -> None:
        for canister in self.canisters:
            move_body(self.gameworld, canister.entity_id, shift)

    def wrap(self, center: Vec2) -> None:
        """ Move canisters to their copy closest to center """
        for canister in self.canisters:
            shift = wrap_shift(canister.pos, center)
            if shift != (0, 0):
                move_body(self.gameworld, canister.entity_id, shift)
