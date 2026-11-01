""" Swarms of rich asteroids passing through the solar system, and what
the player is told about them """

from random import Random
from typing import TYPE_CHECKING

from ...logic.world.bulletin import Bulletin
from ...logic.world.layout import OrbiterPlan
from ...logic.world.space import Celestial
from ...logic.world.swarms import SwarmClock, plan_swarm
from .spots import Spot, spot_of

if TYPE_CHECKING:
    from .solar_system import SolarSystem


class SwarmPassage:

    def __init__(self, system: 'SolarSystem', rng: Random) -> None:
        self.system = system
        self.rng = rng
        self.clock = SwarmClock(rng)
        self.asteroids: list[Celestial] = []
        self.bulletin = Bulletin()

    def update(self, dt: float) -> None:
        system = self.system
        self.asteroids[:] = [
            asteroid for asteroid in self.asteroids
            if asteroid in system.asteroids
        ]
        change = self.clock.update(dt)
        if change == 'arrives':
            self.arrive()
        elif change == 'leaves':
            self.leave()
        self.bulletin.update(dt)

    def arrive(self) -> None:
        plan = plan_swarm(self.rng, self.system.orbits)
        self.add(list(plan.asteroids))

    def add(self, plans: list[OrbiterPlan]) -> None:
        self.asteroids = [
            self.system.add_asteroid(plan, self.system.sun) for plan in plans
        ]

    def leave(self) -> None:
        """ With what wasn't mined """
        for asteroid in list(self.asteroids):
            self.system.remove(asteroid)
        self.asteroids.clear()
        self.bulletin.tell("L'essaim a quitté le système")

    @property
    def headline(self) -> str:
        if self.asteroids and self.clock.passing:
            minutes, seconds = divmod(int(self.clock.left), 60)
            return f'Essaim riche de passage  ·  {minutes}:{seconds:02d}'
        return self.bulletin.shown

    @property
    def spot(self) -> Spot | None:
        return spot_of(self.asteroids)
