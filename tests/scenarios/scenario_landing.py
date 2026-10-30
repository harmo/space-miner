""" Landing on the green ground only, standing on unfolded legs """

import math
from typing import Any

import pytest

from app.logic.ship.config import LANDING_DURATION, LEG_LENGTH
from app.logic.world.space import angle_diff

from .harness import Scenario

scenario = Scenario('landing')
check = scenario.check
remembered: dict[str, Any] = {}


def rear_above_ground() -> float:
    """ Of the ship, standing nose up """
    player = scenario.player
    earth = scenario.game.system.earth
    distance = math.dist(player.ship.position, earth.pos)
    return float(distance - earth.radius - player.stats.size[0] / 2)


def hover(direction: float) -> None:
    earth = scenario.game.system.earth
    scenario.put_ship(scenario.above_earth(direction, 200.), earth.velocity)


@scenario.step(1.)
def starts_landed() -> None:
    scenario.screenshot('earth')
    check(scenario.base.docked, 'the ship starts landed')
    check(scenario.game.looks.gear.unfolded == 1, 'on its legs')
    check(rear_above_ground() == pytest.approx(LEG_LENGTH, abs=.5),
          f'which touch the ground: {rear_above_ground():.1f}')
    check(scenario.player.shortcut == 'hidden', 'no shortcut once landed')
    remembered['touch'] = scenario.hold_towards(scenario.away_from_earth())


@scenario.step(1.)
def takes_off() -> None:
    remembered['touch'].touch_up()
    check(not scenario.base.docked, 'thrusting takes off')
    check(scenario.game.looks.gear.unfolded == 0, 'the legs fold')
    ground = scenario.player.spots(scenario.player.home)
    water = max(
        (math.radians(degrees) for degrees in range(360)),
        key=lambda d: min(abs(angle_diff(spot, d)) for spot in ground),
    )
    hover(water)


@scenario.step(.2)
def not_above_the_water() -> None:
    button = scenario.game.ids.land_button
    check(scenario.player.shortcut == 'aside', 'above the water')
    check(button.disabled and button.text == "Au-dessus de l'eau",
          'the shortcut says so, and can not be used')
    scenario.press(button)


@scenario.step(.2)
def above_the_ground() -> None:
    check(scenario.player.landing is None, 'no landing in the water')
    ground = scenario.player.spots(scenario.player.home)
    hover(ground[len(ground) // 2])


@scenario.step(.2)
def lands() -> None:
    check(scenario.player.shortcut == 'ready', 'ready above the ground')
    scenario.press(scenario.game.ids.land_button)


@scenario.step(LANDING_DURATION * .8)
def unfolds_its_legs() -> None:
    check(scenario.player.landing is not None, 'landing')
    check(scenario.game.looks.gear.unfolded > .5, 'the legs unfold to land')


@scenario.step(LANDING_DURATION * .5)
def landed() -> None:
    check(scenario.player.parking is not None, 'parked once landed')
    check(scenario.base.docked, 'at the base')
    check(rear_above_ground() == pytest.approx(LEG_LENGTH, abs=.5),
          'standing on its legs')


scenario.run()
