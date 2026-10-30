""" The heat of the sun: close to it the hull heats up as its gauge shows,
overheating is told, then the ship blows up and comes back cool. Heavily
shielded, it stays cool there. """

import pytest

from app.logic.ship.config import HEAT_COOLING, RESPAWN_DELAY
from app.logic.ship.heat import heating
from app.logic.ship.shipyard import Design

from .harness import Scenario

scenario = Scenario('heat')
check = scenario.check
DISTANCE = 1000.              # from the sun surface, inside the first orbit


def near_the_sun() -> None:
    sun = scenario.game.system.sun
    x, y = sun.pos
    scenario.put_ship((x + sun.radius + DISTANCE, y), (0., 0.))


@scenario.step(1.)
def flies_close_to_the_sun() -> None:
    check(scenario.game.ids.heat.opacity == 0, 'no heat gauge on the Earth')
    scenario.player.miner.ore['iron'] = 10.
    near_the_sun()


@scenario.step(1.5)
def heats_up() -> None:
    heat = scenario.player.hull.heat
    expected = 1.5 * (heating(DISTANCE) - HEAT_COOLING)
    check(heat == pytest.approx(expected, rel=.3),
          f'the hull heats up: {heat:.3f}, {expected:.3f} expected')
    check(scenario.game.ids.heat.opacity == 1, 'as its gauge shows')
    near_the_sun()
    scenario.player.hull.heat = .85


@scenario.step(.2)
def overheats() -> None:
    message = scenario.game.ids.message_label.text
    check(message == 'Surchauffe !', f'overheating is told: {message!r}')
    scenario.screenshot('overheating')
    scenario.player.hull.heat = .999


@scenario.step(.5)
def blows_up() -> None:
    player = scenario.player
    check(player.ship is None, 'too hot, the ship blows up')
    check(bool(player.canisters.canisters), 'its cargo flying away')


@scenario.step(RESPAWN_DELAY + .5)
def comes_back_cool() -> None:
    player = scenario.player
    check(player.ship is not None and player.hull.heat == 0.,
          'a new ship, cool')
    player.restart(Design(parts={'internal': 'heavy_shield'}))
    near_the_sun()


@scenario.step(1.5)
def stays_cool_shielded() -> None:
    player = scenario.player
    check(player.stats.shield == .75, 'a heavy shield is fitted')
    check(player.hull.heat == 0., f'the hull stays cool: {player.hull.heat}')
    scenario.screenshot('shielded')


scenario.run()
