""" A comet passing through the solar system, one at a time: what it sheds
on its way, what the player is told, and how it is saved """

import math
from random import Random
from typing import TYPE_CHECKING

from ...logic.world.comets import (
    CometClock,
    CometOrbit,
    debris_shed,
    plan_comet,
    plan_debris,
)
from ...logic.world.space import Celestial
from ...logic.world.state import CometState

if TYPE_CHECKING:
    from .solar_system import SolarSystem


class CometPassage:

    def __init__(self, system: 'SolarSystem', rng: Random) -> None:
        self.system = system
        self.rng = rng
        self.clock = CometClock(rng)
        self.comet: Celestial | None = None
        self.orbit: CometOrbit | None = None    # of the comet
        self.debris: list[Celestial] = []       # around it, those left
        self.shed = 0             # asteroids by it, mined or not

    def update(self, dt: float) -> None:
        """ Gone once back at the far end, with what it shed on its way """
        comet, orbit = self.comet, self.orbit
        if comet is None or orbit is None:
            if self.clock.due(dt):
                system = self.system
                self.arrive(plan_comet(self.rng, system.sun, system.orbits))
        elif orbit.over:
            self.leave()
        else:
            self.thaw(comet)

    def arrive(self, orbit: CometOrbit) -> None:
        self.orbit = orbit
        self.comet = self.system.add_comet(orbit)

    def leave(self) -> None:
        system = self.system
        for asteroid in self.debris:
            if asteroid in system.asteroids:
                system.remove(asteroid)
        self.debris.clear()
        self.shed = 0
        if self.comet is not None:
            system.remove(self.comet)
        self.comet = self.orbit = None

    def thaw(self, comet: Celestial) -> None:
        """ It sheds more as it gets closer to the sun """
        system = self.system
        self.debris[:] = [a for a in self.debris if a in system.asteroids]
        distance = math.dist(comet.pos, system.sun.pos) - system.sun.radius
        while self.shed < debris_shed(distance):
            self.debris.append(system.add_asteroid(
                plan_debris(self.rng, self.shed), comet,
            ))
            self.shed += 1

    def state(self) -> CometState | None:
        orbit = self.orbit
        if orbit is None:
            return None
        return CometState(
            orbit.anomaly, orbit.tilt, orbit.sense, self.shed,
            [self.system.plan_now(asteroid) for asteroid in self.debris],
        )

    def resume(self, state: CometState | None) -> None:
        if state is None:
            return
        system = self.system
        orbit = plan_comet(self.rng, system.sun, system.orbits)
        orbit.tilt, orbit.sense = state.tilt, state.sense
        orbit.set_anomaly(state.anomaly)
        self.arrive(orbit)
        assert self.comet is not None
        self.shed = state.shed
        self.debris = [
            system.add_asteroid(plan, self.comet) for plan in state.debris
        ]

    @property
    def headline(self) -> str:
        """ When it races by the sun, and when it is gone """
        orbit = self.orbit
        if orbit is None:
            return ''
        closest = orbit.until_closest
        left = closest if closest > 0 else orbit.left
        minutes, seconds = divmod(int(left), 60)
        told = 'près du soleil dans' if closest > 0 else 'repart dans'
        return f'Comète en vue  ·  {told} {minutes}:{seconds:02d}'
