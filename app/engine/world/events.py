""" What happens in the solar system: belts mined out grow back out of the
sight of the ship, and swarms of rich asteroids pass by now and then """

import math
from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

from ...logic.world.config import REGROW_AWAY
from ...logic.world.layout import BeltPlan
from ...logic.world.regrowth import Regrowth
from ...logic.world.space import Celestial, Orbit, Vec2
from ...logic.world.swarms import SwarmClock, plan_swarm

if TYPE_CHECKING:
    from .solar_system import SolarSystem

NEWS_TIME = 6.                # seconds the end of a swarm is told
TRIES = 12                    # places looked at, for one out of sight
SWARM_SIZE = 300.             # around its middle, for its marker


@dataclass(frozen=True)
class Spot:
    """ Somewhere to point at """
    pos: Vec2
    radius: float


class SystemEvents:

    def __init__(self, system: 'SolarSystem', rng: Random) -> None:
        self.system = system
        self.rng = rng
        self.regrowths = [Regrowth(belt.full) for belt in system.belt_plans]
        self.clock = SwarmClock(rng)
        self.swarm: list[Celestial] = []
        self.news = ''
        self.news_left = 0.       # seconds it is shown still

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
        """ Shown at the top of the screen """
        if self.swarm and self.clock.passing:
            minutes, seconds = divmod(int(self.clock.left), 60)
            return f'Essaim riche de passage  ·  {minutes}:{seconds:02d}'
        return self.news if self.news_left > 0 else ''

    @property
    def swarm_spot(self) -> Spot | None:
        if not self.swarm:
            return None
        count = len(self.swarm)
        return Spot((
            sum(asteroid.pos[0] for asteroid in self.swarm) / count,
            sum(asteroid.pos[1] for asteroid in self.swarm) / count,
        ), SWARM_SIZE)
