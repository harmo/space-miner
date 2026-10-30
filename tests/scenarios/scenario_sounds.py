""" Hearing the game: space humming, the engine taking off, the laser
mining, an asteroid breaking up, the crash, the base, the drones of the
ambience fading into one another, a radio call, and silence once the
sounds then the ambience are turned off """

import math
from pathlib import Path
from typing import Any

from app.engine.audio import audio
from app.logic.ambience import CALLS, DRONE_FADE
from app.logic.config import SOUNDS
from app.logic.ship.config import RESPAWN_DELAY

from .harness import Scenario, loneliest

scenario = Scenario('sounds')
check = scenario.check
remembered: dict[str, Any] = {}
played: list[str] = []


def record() -> None:
    """ The sounds played once, from now on """
    play = audio.play

    def recording(name: str, volume: float | None = None) -> None:
        played.append(name)
        play(name, volume)
    audio.play = recording  # type: ignore[method-assign]


def loops() -> dict[str, Any]:
    soundtrack = scenario.game.soundtrack
    return {
        'drones': {loop.name for loop in soundtrack.drones} - {None},
        'engine': soundtrack.engine.name,
        'laser': soundtrack.laser.name,
        'unloading': soundtrack.unloading.name,
    }


def loaded(name: str) -> bool:
    """ Decoded, or being decoded, by the mixer """
    path = Path(SOUNDS) / f'{name}.ogg'
    mixer = audio.mixer
    return mixer is not None and (
        path in mixer.chunks or path in mixer.decoding
    )


@scenario.step(1.)
def hums_landed() -> None:
    record()
    ambience = scenario.game.soundtrack.ambience
    check(loops() == {
        'drones': {ambience.current}, 'engine': 'engine_hull',
        'laser': None, 'unloading': None,
    }, f'space hums, the engine is ready: {loops()}')
    check(scenario.game.soundtrack.volume == 0, 'and silent')
    check(audio.mixer is not None, 'loops play on the channels of the mixer')
    check(all(drone.playing for drone in scenario.game.soundtrack.drones
              if drone.name), 'space hums for real')
    check(loaded(ambience.upcoming), 'the next drone is decoded aside')
    remembered['touch'] = scenario.hold_towards(scenario.away_from_earth())


@scenario.step(1.)
def takes_off() -> None:
    remembered['touch'].touch_up()
    check('gear_in' in played, f'the legs fold: {played}')
    check(scenario.game.soundtrack.volume > .5, 'the engine roars')
    rock = loneliest(scenario.game.system.asteroids)
    remembered['rock'] = rock
    x, y = rock.pos
    scenario.put_ship((x + 140, y), rock.velocity, angle=math.pi)
    scenario.player.miner.lock_on(rock, scenario.player.ship.position)


@scenario.step(1.)
def mines() -> None:
    check(loops()['laser'] == 'laser_1', f'the laser fires: {loops()}')
    check(scenario.game.soundtrack.laser.playing, 'it is heard')


@scenario.step(4.)
def mines_it_out() -> None:
    gone = remembered['rock'] not in scenario.game.system.asteroids
    check(gone and 'break_rock' in played, f'the rock breaks up: {played}')
    check(loops()['laser'] is None, 'the laser stops')


@scenario.step(.1)
def crashes() -> None:
    asteroid = scenario.game.system.asteroids[0]
    x, y = asteroid.pos
    vx, vy = asteroid.velocity
    scenario.put_ship(
        (x + asteroid.radius + 25, y), (vx - 400, vy), angle=3.14,
    )


@scenario.step(.5)
def explodes() -> None:
    check('explosion' in played, f'the ship explodes: {played}')
    check(loops()['engine'] is None, 'its engine is gone')


@scenario.step(RESPAWN_DELAY + .5)
def trades() -> None:
    check('touchdown' not in played, 'the new ship lands silently')
    base = scenario.base
    scenario.player.miner.ore['iron'] = 20.
    base.unload()
    base.depot.stock['rock'] = 10.
    base.ids.market.sell('rock')


@scenario.step(.5)
def hears_the_base() -> None:
    check(loops()['unloading'] == 'unloading', f'ore unloads: {loops()}')
    check('sale' in played, f'the rock is sold: {played}')
    ambience = scenario.game.soundtrack.ambience
    remembered['drones'] = ambience.current, ambience.upcoming
    ambience.alone = 0.                     # time to fade


@scenario.step(1.)
def fades_into_the_next_drone() -> None:
    current, upcoming = remembered['drones']
    check(loops()['drones'] == {current, upcoming},
          f'both drones are heard: {loops()}')
    check(all(drone.playing for drone in scenario.game.soundtrack.drones),
          'for real')
    scenario.game.soundtrack.ambience.fading = DRONE_FADE - .05


@scenario.step(.5)
def hears_the_next_drone_alone() -> None:
    current, upcoming = remembered['drones']
    ambience = scenario.game.soundtrack.ambience
    check(loops()['drones'] == {upcoming}, f'once faded: {loops()}')
    check(not loaded(current), 'the previous drone is freed')
    check(loaded(ambience.upcoming), 'and another one decoded aside')
    ambience.call_in = 0.


@scenario.step(.5)
def hears_a_radio_call() -> None:
    check(any(name in CALLS for name in played), f'a call: {played}')
    scenario.game.preferences.sounds = 0.


@scenario.step(.5)
def falls_silent() -> None:
    check(audio.volume == 0, 'the sounds are off')
    quiet = loops()
    check(bool(quiet.pop('drones')) and set(quiet.values()) == {None},
          f'all is quiet but space: {loops()}')
    scenario.game.preferences.ambience = 0.


@scenario.step(.5)
def space_falls_silent() -> None:
    check(loops()['drones'] == set(), f'all is quiet: {loops()}')
    check(not any(drone.playing for drone in scenario.game.soundtrack.drones),
          'space too')


scenario.run()
