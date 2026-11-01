""" Riding a comet: the ship holds on to it, is carried along without
burning any fuel, racing towards the sun as the hull heats up, lets go by
thrusting, and is let go when the comet leaves """

import math
from typing import Any

from app.engine.entities import get_body
from app.logic.ship.config import LANDING_DURATION

from .harness import Scenario

scenario = Scenario('comet_ride')
check = scenario.check
remembered: dict[str, Any] = {}
played = scenario.record_sounds()


def comet() -> Any:
    return scenario.game.system.events.comets.comet


def orbit() -> Any:
    return scenario.game.system.events.comets.orbit


def jump(anomaly: float) -> None:
    """ Along its way, its body along with it """
    orbit().anomaly = anomaly
    orbit().along = orbit().solved()
    get_body(scenario.game.gameworld, comet().entity_id).position = (
        orbit().position
    )


def without_debris() -> None:
    """ Nothing to bump into, on the way to it: riding is what is tested """
    system = scenario.game.system
    events = system.events
    for asteroid in list(events.comets.debris):
        system.remove(asteroid)
    events.comets.debris.clear()
    events.comets.shed = 1000


def beside() -> None:
    x, y = comet().pos
    scenario.put_ship((x + 170, y), comet().velocity, angle=0.)


@scenario.step(1.)
def waits_for_a_comet() -> None:
    scenario.game.system.events.comets.clock.waiting = 0.


@scenario.step(.3)
def comes_close() -> None:
    check(comet() is not None, 'a comet comes')
    remembered['grounds'] = len(scenario.player.grounds.grounds) - 1
    without_debris()
    jump(-2.6)                # away from the planet it comes from
    beside()


@scenario.step(.2)
def can_hold_on() -> None:
    button = scenario.game.ids.land_button
    check(button.text == "S'accrocher", f'told: {button.text}')
    check(scenario.player.shortcut == 'ready', 'close enough')
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def holds_on() -> None:
    player = scenario.player
    check(player.parking is not None and player.parking.body is comet(),
          'held on to the comet')
    check('dock' in played, f'heard: {played}')
    remembered['fuel'] = player.tank.level
    remembered['from'] = comet().pos
    remembered['distance'] = math.dist(player.ship.position, comet().pos)


@scenario.step(2.)
def is_carried_along() -> None:
    player = scenario.player
    check(math.dist(comet().pos, remembered['from']) > 20, 'the comet moves')
    distance = math.dist(player.ship.position, comet().pos)
    check(abs(distance - remembered['distance']) < 2,
          f'the ship along with it: {distance:.0f}')
    check(player.tank.level == remembered['fuel'], 'for free')
    jump(-.03)
    player.heat.level = 0.


@scenario.step(1.)
def races_towards_the_sun() -> None:
    player = scenario.player
    speed = math.hypot(*player.ship.velocity)
    check(speed > player.stats.max_speed, f'faster than ever: {speed:.0f}')
    check(player.heat.level > 0, f'the hull heats up: {player.heat.level}')
    scenario.screenshot('riding')
    jump(-2.5)
    player.heat.level = 0.
    remembered['touch'] = scenario.hold_towards(0.)


@scenario.step(.5)
def thrusting_lets_go() -> None:
    remembered['touch'].touch_up()
    check(scenario.player.parking is None, 'let go by thrusting')
    check(scenario.player.ship is not None, 'safe and sound')
    beside()


@scenario.step(.2)
def holds_on_again() -> None:
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def rides_until_the_end() -> None:
    check(scenario.player.parking is not None, 'held on again')
    jump(math.pi - .001)


@scenario.step(.5)
def is_let_go_when_it_leaves() -> None:
    player = scenario.player
    check(comet() is None, 'the comet left')
    check(player.parking is None, 'letting go of the ship')
    check(player.ship is not None, 'which flies on')
    check(len(player.grounds.grounds) == remembered['grounds'],
          'nothing left to hold on to')
    button = scenario.game.ids.land_button
    check(button.text != "S'accrocher" or button.opacity == 0,
          f'nothing to hold on to: {button.text}')


scenario.run()
