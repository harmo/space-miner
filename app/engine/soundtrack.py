""" The sounds of the game, on each frame: space humming all around, the
engine following the thrust, the laser while it fires, the ore unloaded,
and what happened since the previous frame. The game standing still, only
space goes on humming. """

from typing import TYPE_CHECKING

from ..logic.sounds import (
    Moment,
    break_sound,
    engine_sound,
    heard,
    laser_sound,
    toward,
)
from .audio import Loop, audio
from .ship.player import Player

if TYPE_CHECKING:
    from .game import Game


class Soundtrack:

    def __init__(self, player: Player) -> None:
        self.ambient = Loop(audio)
        self.engine = Loop(audio)
        self.laser = Loop(audio)
        self.unloading = Loop(audio)
        self.volume = 0.                    # of the engine
        self.moment: Moment | None = None   # on the previous frame
        miner = player.miner
        miner.on_mined_out.append(lambda name: audio.play(break_sound(name)))
        miner.on_pick_up.append(lambda: audio.play('pickup'))

    def update(self, game: 'Game', dt: float, heading: float | None) -> None:
        audio.muted = not game.preferences.sound
        self.ambient.play('ambient')
        player, base = game.player, game.ids.base
        moment = Moment(
            ship=player.ship.entity_id if player.ship else None,
            parked=player.parking is not None,
            legs_out=game.looks.gear.out,
            cargo_full=player.miner.cargo_full,
            credits=base.wallet.credits,
            validated=base.board.validated if base.board else 0,
            swarm=bool(game.system.events.swarm),
        )
        running = game.playing and not game.map_open
        if running and self.moment is not None:
            for name in heard(self.moment, moment):
                audio.play(name)
        self.moment = moment
        if not running:
            self.volume = 0.
            for loop in (self.engine, self.laser, self.unloading):
                loop.stop()
            return
        thrust = game.looks.exhaust.thrust(player, heading)
        self.volume = toward(self.volume, thrust, dt)
        self.engine.play(
            engine_sound(player.design) if player.ship else None,
            self.volume,
        )
        firing = player.miner.firing
        self.laser.play(laser_sound(player.stats.laser) if firing else None)
        self.unloading.play('unloading' if base.unloading else None)
