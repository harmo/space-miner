""" What happens in the solar system: belts mined out grow back out of the
sight of the ship, swarms of rich asteroids and comets pass by now and
then, and the sun flares, see flares.py """

import math
from random import Random
from typing import TYPE_CHECKING

from ...logic.colors import Rgb
from ...logic.config import COMET_COLOR, FLARE_COLOR, SWARM_COLOR
from ...logic.world.comets import (
    CometClock,
    CometOrbit,
    debris_shed,
    plan_comet,
    plan_debris,
)
from ...logic.world.config import REGROW_AWAY
from ...logic.world.layout import BeltPlan
from ...logic.world.regrowth import Regrowth
from ...logic.world.space import Celestial, Orbit, Vec2
from ...logic.world.state import CometState, EventsState
from ...logic.world.swarms import SwarmClock, plan_swarm
from .flares import SolarFlares
from .spots import Spot, spot_of

if TYPE_CHECKING:
    from .solar_system import SolarSystem

NEWS_TIME = 6.                # seconds the end of a swarm is told
TRIES = 12                    # places looked at, for one out of sight


class SystemEvents:

    def __init__(self, system: 'SolarSystem', rng: Random) -> None:
        self.system = system
        self.rng = rng
        self.regrowths: list[Regrowth] = []
        for belt in system.belt_plans:
            self.watch(belt)
        self.clock = SwarmClock(rng)
        self.flares = SolarFlares(system, rng)
        self.comet_clock = CometClock(rng)
        self.comet: Celestial | None = None
        self.debris: list[Celestial] = []   # around it, those left
        self.shed = 0             # asteroids by it, mined or not
        self.swarm: list[Celestial] = []
        self.news = ''
        self.news_left = 0.       # seconds it is shown still

    def watch(self, belt: BeltPlan) -> None:
        """ Growing back as it should """
        self.regrowths.append(
            Regrowth(belt.full, belt.regrow_time, belt.regrow_below)
        )

    def update(self, dt: float, ship: Vec2) -> None:
        system = self.system
        for plan, belt, regrowth in zip(
            system.belt_plans, system.belts, self.regrowths, strict=True,
        ):
            for _ in range(regrowth.update(len(belt), dt)):
                belt.append(self.grow(plan, ship))
        self.swarm[:] = [
            asteroid for asteroid in self.swarm
            if asteroid in system.asteroids
        ]
        change = self.clock.update(dt)
        if change == 'arrives':
            self.arrive()
        elif change == 'leaves':
            self.leave()
        self.news_left = max(0., self.news_left - dt)
        self.flares.update(dt)
        self.update_comet(dt)

    def update_comet(self, dt: float) -> None:
        """ One at a time, gone once back at the far end, with what it
        shed on its way """
        system, comet = self.system, self.comet
        orbit = self.comet_orbit
        if comet is None or orbit is None:
            if self.comet_clock.due(dt):
                self.comet = system.add_comet(
                    plan_comet(self.rng, system.sun, system.orbits)
                )
            return
        if orbit.over:
            for asteroid in self.debris:
                if asteroid in system.asteroids:
                    system.remove(asteroid)
            self.debris.clear()
            self.shed = 0
            system.remove(comet)
            self.comet = None
            return
        self.debris[:] = [a for a in self.debris if a in system.asteroids]
        distance = math.dist(comet.pos, system.sun.pos) - system.sun.radius
        while self.shed < debris_shed(distance):
            self.debris.append(system.add_asteroid(
                plan_debris(self.rng, self.shed), comet,
            ))
            self.shed += 1

    def state(self) -> EventsState:
        """ To save """
        system, flares, clock = self.system, self.flares, self.clock
        orbit = self.comet_orbit
        comet = None
        if orbit is not None:
            comet = CometState(
                orbit.anomaly, orbit.tilt, orbit.sense, self.shed,
                [system.plan_now(asteroid) for asteroid in self.debris],
            )
        return EventsState(
            flares.clock.phase, flares.clock.left,
            [system.plan_now(asteroid) for asteroid in flares.ejecta],
            clock.waiting, clock.left,
            [system.plan_now(asteroid) for asteroid in self.swarm],
            self.comet_clock.waiting, comet,
        )

    def resume(self, state: EventsState) -> None:
        """ As it was saved, on a solar system with nothing going on """
        system, flares, clock = self.system, self.flares, self.clock
        sun = system.sun
        flares.clock.phase, flares.clock.left = (
            state.flare_phase, state.flare_left,
        )
        flares.ejecta = [
            system.add_asteroid(plan, sun) for plan in state.ejecta
        ]
        clock.waiting, clock.left = state.swarm_waiting, state.swarm_left
        self.swarm = [system.add_asteroid(plan, sun) for plan in state.swarm]
        self.comet_clock.waiting = state.comet_waiting
        comet = state.comet
        if comet is not None:
            orbit = plan_comet(self.rng, sun, system.orbits)
            orbit.tilt, orbit.sense = comet.tilt, comet.sense
            orbit.set_anomaly(comet.anomaly)
            self.comet = system.add_comet(orbit)
            self.shed = comet.shed
            self.debris = [
                system.add_asteroid(plan, self.comet) for plan in comet.debris
            ]

    @property
    def comet_orbit(self) -> CometOrbit | None:
        orbit = self.comet.orbit if self.comet else None
        return orbit if isinstance(orbit, CometOrbit) else None

    def grow(self, belt: BeltPlan, ship: Vec2) -> Celestial:
        """ One asteroid back, as far from the ship as can be found """
        parent = self.system.parent_of(belt)
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

    def arrive(self) -> None:
        plan = plan_swarm(self.rng, self.system.orbits)
        self.swarm = [
            self.system.add_asteroid(asteroid, self.system.sun)
            for asteroid in plan.asteroids
        ]

    def leave(self) -> None:
        """ With what wasn't mined """
        for asteroid in list(self.swarm):
            self.system.remove(asteroid)
        self.swarm.clear()
        self.news = "L'essaim a quitté le système"
        self.news_left = NEWS_TIME

    @property
    def headline(self) -> str:
        """ Shown at the top of the screen, the flares first """
        if self.flares.headline:
            return self.flares.headline
        if self.comet_orbit is not None:
            return comet_news(self.comet_orbit)
        if self.swarm and self.clock.passing:
            minutes, seconds = divmod(int(self.clock.left), 60)
            return f'Essaim riche de passage  ·  {minutes}:{seconds:02d}'
        return self.news if self.news_left > 0 else ''

    @property
    def headline_color(self) -> Rgb:
        if self.flares.headline:
            return FLARE_COLOR
        return COMET_COLOR if self.comet_orbit else SWARM_COLOR

    @property
    def swarm_spot(self) -> Spot | None:
        return spot_of(self.swarm)


def comet_news(orbit: CometOrbit) -> str:
    """ When it races by the sun, and when it is gone """
    closest = orbit.until_closest
    left = closest if closest > 0 else orbit.left
    minutes, seconds = divmod(int(left), 60)
    told = 'près du soleil dans' if closest > 0 else 'repart dans'
    return f'Comète en vue  ·  {told} {minutes}:{seconds:02d}'
