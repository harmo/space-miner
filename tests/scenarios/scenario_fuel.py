""" Burning fuel: taking off empties the tank as the gauge shows, and out of
it the ship can neither thrust nor mine, until saved as it is """

import json
import math
import os
from typing import Any

import pytest

from .harness import Scenario, loneliest

scenario = Scenario('fuel')
check = scenario.check
remembered: dict[str, Any] = {}


@scenario.step(1.)
def starts_full() -> None:
    tank = scenario.player.tank
    check(tank.share == 1., f'the tank is full: {tank.level}')
    check(scenario.game.ids.fuel.amount == '100 %', 'as the gauge shows')
    remembered['touch'] = scenario.hold_towards(scenario.away_from_earth())


@scenario.step(1.5)
def burns_taking_off() -> None:
    remembered['touch'].touch_up()
    player = scenario.player
    burnt = player.tank.capacity - player.tank.level
    check(burnt == pytest.approx(1.5 * player.stats.burn, rel=.2),
          f'thrusting burns fuel: {burnt:.2f}')
    check(scenario.game.ids.fuel.fill < 1., 'the gauge goes down')
    scenario.screenshot('gauge')
    player.tank.level = .2
    remembered['touch'] = scenario.hold_towards(0.)


@scenario.step(1.)
def runs_dry() -> None:
    player = scenario.player
    check(player.tank.empty, 'the tank runs dry')
    check(player.thrust(0.) == 0., 'the ship no longer thrusts')
    message = scenario.game.ids.message_label.text
    check(message == 'Panne sèche', f'as told: {message!r}')
    remembered['touch'].touch_up()
    rock = loneliest(scenario.game.system.asteroids)
    x, y = rock.pos
    scenario.put_ship((x + 140, y), rock.velocity, angle=math.pi)
    player.miner.lock_on(rock, player.ship.position)


@scenario.step(.5)
def cannot_mine() -> None:
    miner = scenario.player.miner
    check(not miner.busy and not miner.firing, 'nor mine')
    scenario.game.save()


@scenario.step(.1)
def is_saved_dry() -> None:
    path = os.path.join(scenario.data, 'save.json')
    with open(path, encoding='utf-8') as file:
        fuel = json.load(file)['fuel']
    check(fuel == 0., f'saved with its tank empty: {fuel}')


scenario.run()
