""" The legs of the player's ship: unfolded during the last part of the
landing and while landed, folded once it takes off """

from ...logic.ship.legs import legs, unfold
from ..ui.overlay import Overlay
from .player import Player

UNFOLD_FROM = .5              # of the landing, when the legs come out
HIDDEN = .05                  # folded at least this much, along the hull


class LandingGear:

    def __init__(self) -> None:
        self.unfolded = 1.    # the ship starts landed
        self.out = True       # unfolding or unfolded

    def update(self, player: Player, dt: float) -> None:
        if player.ship is None:
            self.unfolded = 1.            # comes back landed
            self.out = True
            return
        landing = player.landing
        self.out = player.parking is not None or (
            landing is not None and landing.progress > UNFOLD_FROM
        )
        self.unfolded = unfold(self.unfolded, dt, self.out)

    def draw(self, overlay: Overlay, player: Player) -> None:
        ship = player.ship
        if ship is None or self.unfolded < HIDDEN:
            return
        angle = ship.body.angle
        overlay.legs(legs(
            ship.position, angle, ship.stats.size, self.unfolded,
            player.ground_body,
        ), angle)
