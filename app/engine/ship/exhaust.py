""" The exhaust trail of the player's ship: full while thrusting, weaker
while holding in front of what it works on, or landing """

from random import Random

from ...logic.ship.config import TRAIL_HOLDING, TRAIL_LANDING
from ...logic.ship.shipyard import Design
from ...logic.ship.trails import Nozzle, Trail, look, nozzles
from ...logic.world.space import Vec2
from ..ui.overlay import Overlay
from .player import Player


class Exhaust:

    def __init__(self, rng: Random) -> None:
        self.trail = Trail(rng)
        self.design: Design | None = None
        self.nozzles: list[Nozzle] = []     # of that design

    def thrust(self, player: Player, heading: float | None) -> float:
        if player.ship is None or player.parking is not None:
            return 0.
        if player.landing is not None:
            return TRAIL_LANDING
        if player.miner.busy:
            return TRAIL_HOLDING
        return 1. if heading is not None else 0.

    def update(self, player: Player, heading: float | None,
               dt: float) -> None:
        if player.design != self.design:
            self.design = player.design
            self.nozzles = nozzles(player.design)
        ship = player.ship
        if ship is None:
            self.trail.update(dt, (0., 0.), 0., (0., 0.), [], 0.)
            return
        self.trail.update(
            dt, ship.position, ship.body.angle, ship.velocity,
            self.nozzles, self.thrust(player, heading),
        )

    def shift(self, shift: Vec2) -> None:
        self.trail.shift(shift)

    def draw(self, overlay: Overlay) -> None:
        overlay.sparks(
            ((spark.x, spark.y), *look(spark)) for spark in self.trail.sparks
        )
