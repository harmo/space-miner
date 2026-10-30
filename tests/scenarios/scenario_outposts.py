""" Outposts: the site of the Frontier on the farthest planet, where the
ship lands on its pad, and how it looks as it is built """

import math
from typing import Any

from app.logic.ship.config import LANDING_DURATION

from .harness import Scenario

scenario = Scenario('outposts')
check = scenario.check
remembered: dict[str, Any] = {}


def frontier() -> Any:
    return scenario.game.outposts[0]


@scenario.step(1.)
def flies_to_the_site() -> None:
    outpost = frontier()
    check(outpost.body is scenario.game.system.planets[-1],
          'on the farthest planet')
    check(outpost.construction.built == 0, 'nothing built yet')
    x, y = outpost.pos
    direction = outpost.direction
    scenario.put_ship(
        (x + math.cos(direction) * 150, y + math.sin(direction) * 150),
        outpost.body.velocity, angle=direction,
    )


@scenario.step(.3)
def sees_the_bare_site() -> None:
    scenario.screenshot('site')
    shortcut = scenario.player.shortcut
    check(shortcut == 'ready', f'the landing shortcut is ready: {shortcut}')
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def lands_on_the_pad() -> None:
    player = scenario.player
    outpost = frontier()
    check(player.docked_on(outpost.body), 'landed on the planet')
    check(abs(math.remainder(
        player.parking.direction - outpost.direction, 2 * math.pi,
    )) < math.radians(10), 'on the pad')
    check(not scenario.base.docked, 'not at the base on the Earth')
    frontier().construction.built = 1


@scenario.step(.3)
def shows_the_pad() -> None:
    scenario.screenshot('pad')
    frontier().construction.built = 2


@scenario.step(.3)
def shows_the_habitat() -> None:
    scenario.screenshot('habitat')
    frontier().construction.built = 3


@scenario.step(.3)
def shows_the_trading_post() -> None:
    scenario.screenshot('trading')


scenario.run()
