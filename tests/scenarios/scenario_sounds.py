""" Hearing the game: space humming, the engine taking off, the laser
mining, an asteroid breaking up, the crash, the base, and silence once the
sounds are turned off """

import math
from typing import Any

from app.engine.audio import audio
from app.logic.ship.config import RESPAWN_DELAY

from .harness import Scenario, loneliest

scenario = Scenario('sounds')
check = scenario.check
remembered: dict[str, Any] = {}
played: list[str] = []


def record() -> None:
    """ The sounds played once, from now on """
    play = audio.play

    def recording(name: str) -> None:
        played.append(name)
        play(name)
    audio.play = recording  # type: ignore[method-assign]


def loops() -> dict[str, str | None]:
    soundtrack = scenario.game.soundtrack
    return {
        'ambient': soundtrack.ambient.name,
        'engine': soundtrack.engine.name,
        'laser': soundtrack.laser.name,
        'unloading': soundtrack.unloading.name,
    }


@scenario.step(1.)
def hums_landed() -> None:
    record()
    check(loops() == {
        'ambient': 'ambient', 'engine': 'engine_hull', 'laser': None,
        'unloading': None,
    }, f'space hums, the engine is ready: {loops()}')
    check(scenario.game.soundtrack.volume == 0, 'and silent')
    check(audio.mixer is not None, 'loops play on the channels of the mixer')
    check(scenario.game.soundtrack.ambient.playing, 'space hums for real')
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
    scenario.game.preferences.sounds = 0.


@scenario.step(.5)
def falls_silent() -> None:
    check(audio.volume == 0, 'the sounds are off')
    check(set(loops().values()) == {'ambient', None},
          f'all is quiet but space: {loops()}')
    scenario.game.preferences.ambience = 0.


@scenario.step(.5)
def space_falls_silent() -> None:
    check(set(loops().values()) == {None}, f'all is quiet: {loops()}')
    check(not scenario.game.soundtrack.ambient.playing, 'space too')


scenario.run()
