""" The sounds of the game, on each frame: drones of the ambience fading
into one another and radio calls, the engine following the thrust, the
laser while it fires, the ore unloaded, and what happened since the
previous frame. The game standing still, only the drones go on. The
ambience and the other sounds each have their own volume, chosen in the
settings. """

from random import Random
from typing import TYPE_CHECKING

from ..logic.ambience import Ambience
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

    def __init__(self, player: Player, rng: Random) -> None:
        self.ambience = Ambience(rng)
        self.drones = [Loop(audio), Loop(audio)]    # fading into each other
        self.engine = Loop(audio)
        self.laser = Loop(audio)
        self.unloading = Loop(audio)
        self.volume = 0.                    # of the engine
        self.moment: Moment | None = None   # on the previous frame
        miner = player.miner
        miner.on_mined_out.append(lambda name: audio.play(break_sound(name)))
        miner.on_pick_up.append(lambda: audio.play('pickup'))

    def update(self, game: 'Game', dt: float, heading: float | None) -> None:
        preferences = game.preferences
        audio.volume = sounds = preferences.sounds
        playing = game.playing and not game.map_open
        self.hum(preferences.ambience, dt, playing)
        player, base = game.player, game.ids.base
        moment = Moment(
            ship=player.spawned if player.ship else None,
            parked=player.parking is not None,
            legs_out=game.looks.gear.out,
            cargo_full=player.miner.cargo_full,
            credits=base.wallet.credits,
            validated=base.board.validated if base.board else 0,
            swarm=bool(game.system.events.swarm),
            fuel=player.tank.level,
            gauge=player.tank.gauge,
            stranded=player.stranded,
        )
        running = playing and sounds > 0
        if running and self.moment is not None:
            for name in heard(self.moment, moment):
                audio.play(name)
        self.moment = moment
        if not running:
            self.volume = 0.
            for loop in (self.engine, self.laser, self.unloading):
                loop.stop()
            return
        thrust = player.thrust(heading)
        self.volume = toward(self.volume, thrust, dt)
        self.engine.play(
            engine_sound(player.design) if player.ship else None,
            self.volume * sounds,
        )
        firing = player.miner.firing
        self.laser.play(
            laser_sound(player.stats.laser) if firing else None, sounds,
        )
        # One machine of the base at a time, unloading first
        machine = 'unloading' if base.unloading else (
            'crushing' if base.crushing and base.docked else None
        )
        self.unloading.play(machine, sounds)

    def hum(self, volume: float, dt: float, playing: bool) -> None:
        """ The drones of the ambience, the next one decoded aside before
        its turn, and radio calls while playing """
        if volume <= 0:
            for loop in self.drones:
                self.silence(loop)
            return
        ambience = self.ambience
        ambience.update(dt)
        audio.preload(ambience.upcoming)
        volumes = ambience.volumes
        for loop in self.drones:
            if loop.name not in volumes:
                self.silence(loop)
        for name, share in volumes.items():
            loop = next(
                (loop for loop in self.drones if loop.name == name), None,
            ) or next(loop for loop in self.drones if loop.name is None)
            loop.play(name, share * volume)
        call = ambience.call(dt) if playing else None
        if call is not None:
            audio.play(call, volume)

    def silence(self, drone: Loop) -> None:
        """ Freeing the drone it played, unless it comes back soon """
        name = drone.name
        drone.stop()
        ambience = self.ambience
        if name is not None and name not in (
            ambience.current, ambience.upcoming,
        ):
            audio.release(name)
