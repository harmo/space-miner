""" What is drawn around the player's ship, over the game: its exhaust
trail and its landing legs """

from random import Random

from ...logic.world.space import Vec2
from .exhaust import Exhaust
from .landing_gear import LandingGear
from .player import Player


class ShipLooks:

    def __init__(self, rng: Random) -> None:
        self.exhaust = Exhaust(rng)
        self.gear = LandingGear()

    def update(
        self,
        player: Player,
        heading: float | None,
        dt: float
    ) -> None:
        self.exhaust.update(player, heading, dt)
        self.gear.update(player, dt)

    def shift(self, shift: Vec2) -> None:
        self.exhaust.shift(shift)
