""" Burning fuel: taking off empties the tank as the gauge shows, and out of
it the ship can neither thrust nor mine. Saved as it is, it calls for help
and is towed back to the Earth, where its tank is filled with the ice of
its cargo then credits, or given a reserve without any. """

import json
import math
import os
from typing import Any

import pytest

from app.logic.base.config import FREE_RESERVE, FUEL_PRICE, ICE_FUEL

from .harness import Scenario, loneliest

scenario = Scenario('fuel')
check = scenario.check
remembered: dict[str, Any] = {}
played = scenario.record_sounds()


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
    check(played[-2:] == ['low_fuel', 'fuel_out'],
          f'heard running low, then dry: {played}')
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
    base = scenario.base
    base.wallet.credits = 1000
    scenario.player.miner.ore.update({'iron': 5., 'ice': 10.})


@scenario.step(.2)
def calls_for_help() -> None:
    base, button = scenario.base, scenario.game.ids.distress_button
    check(base.stranded and button.opacity == 1, 'help can be called')
    check(base.tow_cost in button.text, f'for a price: {button.text!r}')
    remembered['price'] = base.tow_price
    scenario.screenshot('stranded')
    scenario.press(button)


@scenario.step(.5)
def is_towed_back_and_refuelled() -> None:
    base, player = scenario.base, scenario.player
    check(base.docked, 'towed back onto the Earth')
    check(player.miner.ore == {'iron': 5.}, f'with its cargo, but the ice'
          f' burnt: {player.miner.ore}')
    check(player.tank.share == 1., f'the tank is full: {player.tank.level}')
    check(played[-2:] == ['tow', 'refuel'],
          f'heard towed back, then filled: {played}')
    paid = (player.tank.capacity - 10. * ICE_FUEL) * FUEL_PRICE
    expected = 1000 - remembered['price'] - paid
    check(base.wallet.credits == expected,
          f'paid the tow and fuel: {base.wallet.credits} for {expected}')
    base.wallet.credits = 0
    player.tank.level = 0.


@scenario.step(.2)
def is_given_a_reserve_when_broke() -> None:
    share = scenario.player.tank.share
    check(share == pytest.approx(FREE_RESERVE), f'a reserve: {share:.2f}')


scenario.run()
