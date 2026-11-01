""" What happens in the solar system: belts mined out grow back out of the
sight of the ship, swarms and comets pass by now and then, and the sun
flares, see swarm_passage.py, comet_passage.py and flares.py """

import math
from random import Random
from typing import TYPE_CHECKING

from ...logic.colors import Rgb
from ...logic.config import COMET_COLOR, FLARE_COLOR, SWARM_COLOR
from ...logic.world.config import REGROW_AWAY
from ...logic.world.layout import BeltPlan
from ...logic.world.regrowth import Regrowth
from ...logic.world.space import Celestial, Orbit, Vec2
from ...logic.world.state import EventsState
from .comet_passage import CometPassage
from .flares import SolarFlares
from .swarm_passage import SwarmPassage

if TYPE_CHECKING:
    from .solar_system import SolarSystem

TRIES = 12                    # places looked at, for one out of sight


class SystemEvents:

    def __init__(self, system: 'SolarSystem', rng: Random) -> None:
        self.system = system
        self.rng = rng
        self.regrowths: list[Regrowth] = []
        for belt in system.belt_plans:
            self.watch(belt)
        self.swarms = SwarmPassage(system, rng)
        self.flares = SolarFlares(system, rng)
        self.comets = CometPassage(system, rng)

    def watch(self, belt: BeltPlan) -> None:
        """ Growing back as it should """
        self.regrowths.append(
            Regrowth(belt.full, belt.regrow_time, belt.regrow_below)
        )

    def update(self, dt: float, ship: Vec2) -> None:
        system = self.system
        for plan, parent, belt, regrowth in zip(
            system.belt_plans, system.belt_parents, system.belts,
            self.regrowths, strict=True,
        ):
            for _ in range(regrowth.update(len(belt), dt)):
                belt.append(self.grow(plan, parent, ship))
        self.swarms.update(dt)
        self.flares.update(dt)
        self.comets.update(dt)

    def grow(self, belt: BeltPlan, parent: Celestial,
             ship: Vec2) -> Celestial:
        """ One asteroid back, as far from the ship as can be found """
        best, farthest = None, -1.
        for _ in range(TRIES):
            plan = belt.asteroid(self.rng, self.rng.uniform(0, 2 * math.pi))
            pos = Orbit(
                parent, plan.orbit_radius, plan.speed, plan.orbit_angle
            ).position
            distance = math.dist(pos, ship)
            if distance > farthest:
                best, farthest = plan, distance
            if distance >= REGROW_AWAY:
                break
        assert best is not None
        return self.system.add_asteroid(best, parent)

    def state(self) -> EventsState:
        """ To save """
        system, flares, swarms = self.system, self.flares, self.swarms
        return EventsState(
            flares.clock.phase, flares.clock.left,
            [system.plan_now(asteroid) for asteroid in flares.ejecta],
            swarms.clock.waiting, swarms.clock.left,
            [system.plan_now(asteroid) for asteroid in swarms.asteroids],
            self.comets.clock.waiting, self.comets.state(),
        )

    def resume(self, state: EventsState) -> None:
        """ As it was saved, on a solar system with nothing going on """
        system, flares, swarms = self.system, self.flares, self.swarms
        flares.clock.phase, flares.clock.left = (
            state.flare_phase, state.flare_left,
        )
        flares.ejecta = [
            system.add_asteroid(plan, system.sun) for plan in state.ejecta
        ]
        swarms.clock.waiting = state.swarm_waiting
        swarms.clock.left = state.swarm_left
        swarms.add(state.swarm)
        self.comets.clock.waiting = state.comet_waiting
        self.comets.resume(state.comet)

    @property
    def headline(self) -> str:
        """ Shown at the top of the screen, the flares first """
        return (
            self.flares.headline or self.comets.headline
            or self.swarms.headline
        )

    @property
    def headline_color(self) -> Rgb:
        if self.flares.headline:
            return FLARE_COLOR
        return COMET_COLOR if self.comets.headline else SWARM_COLOR
