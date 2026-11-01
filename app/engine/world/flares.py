""" Solar flares in the solar system: the ejecta they leave, as asteroids
around the sun, and what the player is told about them """

from random import Random
from typing import TYPE_CHECKING

from ...logic.world.bulletin import Bulletin
from ...logic.world.flares import FlareClock, plan_ejecta
from ...logic.world.space import Celestial
from .spots import Spot, spot_of

if TYPE_CHECKING:
    from .solar_system import SolarSystem

WAVES = 5                     # leaving the sun while it blazes


class SolarFlares:

    def __init__(self, system: 'SolarSystem', rng: Random) -> None:
        self.system = system
        self.rng = rng
        self.clock = FlareClock(rng)
        self.ejecta: list[Celestial] = []
        self.bulletin = Bulletin()

    @property
    def surge(self) -> float:
        """ Times the heat of the sun """
        return self.clock.surge

    @property
    def wave(self) -> float | None:
        """ How far the current wave went, from 0 at the sun surface to 1,
        while it blazes """
        if self.clock.phase != 'blazing':
            return None
        return self.clock.progress * WAVES % 1

    def update(self, dt: float) -> None:
        self.ejecta[:] = [
            asteroid for asteroid in self.ejecta
            if asteroid in self.system.asteroids
        ]
        change = self.clock.update(dt)
        if change == 'ejects':
            self.eject()
        elif change == 'falls':
            self.fall()
        self.bulletin.update(dt)

    def eject(self) -> None:
        sun = self.system.sun
        self.ejecta = [
            self.system.add_asteroid(asteroid, sun)
            for asteroid in plan_ejecta(self.rng, sun.radius)
        ]

    def fall(self) -> None:
        """ Back into the sun, with what wasn't mined """
        for asteroid in list(self.ejecta):
            self.system.remove(asteroid)
        self.ejecta.clear()
        self.bulletin.tell('Les éjectas sont retombés dans le soleil')

    @property
    def headline(self) -> str:
        """ Shown at the top of the screen """
        clock = self.clock
        minutes, seconds = divmod(int(clock.left), 60)
        if clock.phase == 'warning':
            return f'Éruption solaire dans {minutes}:{seconds:02d}'
        if clock.phase == 'blazing':
            return 'Éruption solaire !'
        if clock.phase == 'ejecta' and self.ejecta:
            return f'Éjectas solaires  ·  {minutes}:{seconds:02d}'
        return self.bulletin.shown

    @property
    def ejecta_spot(self) -> Spot | None:
        return spot_of(self.ejecta)
