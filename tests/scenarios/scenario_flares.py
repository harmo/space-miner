""" A solar flare: told before, it blazes in waves, heating the hull much
more, then leaves ejecta of the rarest ore close to the sun, which fall
back into it """

import math
from typing import Any

from app.logic.world.config import EJECTA_ASTEROIDS, EJECTA_ORBIT, FLARE_BLAZE
from app.logic.world.flares import RICHEST

from .harness import Scenario

scenario = Scenario('flares')
check = scenario.check
remembered: dict[str, Any] = {}
played = scenario.record_sounds()
SOON = .01                    # seconds left in the current phase


def flares() -> Any:
    return scenario.game.system.events.flares


def headline() -> str:
    return str(scenario.game.ids.news.text)


@scenario.step(1.)
def is_quiet() -> None:
    check(flares().clock.phase == 'quiet', 'the sun is quiet')
    flares().clock.left = SOON


@scenario.step(.3)
def warns() -> None:
    check(headline().startswith('Éruption solaire dans'),
          f'the flare is told: {headline()!r}')
    check(played[-1:] == ['flare_warning'], f'and heard: {played}')
    flares().clock.left = SOON


@scenario.step(.1)
def blazes() -> None:
    # At its height in half a second, a wave crossing the ship
    flares().clock.left = FLARE_BLAZE / 2 + 1.2
    sun = scenario.game.system.sun
    x, y = sun.pos
    scenario.put_ship((x + sun.radius + 1600., y), (0., 0.))


@scenario.step(.5)
def heats_much_more() -> None:
    check(headline() == 'Éruption solaire !', f'as told: {headline()!r}')
    check('flare' in played, f'heard blazing: {played}')
    check(flares().surge > 3., f'the heat surges: {flares().surge:.1f}')
    check(flares().wave is not None, 'in waves')
    heat = scenario.player.heat.level
    check(heat > .15, f'the hull heats up fast: {heat:.2f}')
    scenario.screenshot('waves')
    # Back to the Earth, away from the heat
    earth = scenario.game.system.earth
    scenario.put_ship(scenario.above_earth(0., 400.), earth.velocity)
    flares().clock.left = SOON


@scenario.step(.3)
def ejects_the_rarest_ore() -> None:
    ejecta = flares().ejecta
    check(len(ejecta) == EJECTA_ASTEROIDS, f'ejecta: {len(ejecta)}')
    check(all(asteroid.mineral in RICHEST for asteroid in ejecta),
          'of the rarest ore')
    sun = scenario.game.system.sun
    farthest = max(
        math.dist(asteroid.pos, sun.pos) - sun.radius for asteroid in ejecta
    )
    check(farthest <= EJECTA_ORBIT[1] + 1, f'close to the sun: {farthest}')
    check(headline().startswith('Éjectas solaires'), f'told: {headline()!r}')
    check(flares().ejecta_spot is not None, 'pointed at')
    remembered['ejecta'] = list(ejecta)
    flares().clock.left = SOON


@scenario.step(.3)
def they_fall_back() -> None:
    asteroids = scenario.game.system.asteroids
    check(not any(a in asteroids for a in remembered['ejecta']),
          'into the sun')
    check(headline() == 'Les éjectas sont retombés dans le soleil',
          f'as told: {headline()!r}')


scenario.run()
