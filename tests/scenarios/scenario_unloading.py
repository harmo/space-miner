""" Unloading the cargo into the depot, stopped by taking off """

from typing import Any

import pytest

from app.logic.base.config import DEPOT_CAPACITY, UNLOAD_RATE

from .harness import Scenario

scenario = Scenario('unloading')
check = scenario.check
CARGO = {'rock': 20., 'iron': 12.5, 'gold': 6.}


@scenario.step(1.)
def fills_the_cargo() -> None:
    scenario.player.miner.ore.update(CARGO)


@scenario.step(.3)
def unloads() -> None:
    check(scenario.base.can_unload, 'a full cargo can be unloaded')
    scenario.press(scenario.base.ids.unload_button)


@scenario.step(1.)
def unloading() -> None:
    base = scenario.base
    check(base.unloading, 'unloading')
    moved = sum(base.depot.stock.values())
    check(moved == pytest.approx(UNLOAD_RATE, rel=.25),
          f'at its rate: {moved:.1f} in a second')
    check(list(base.depot.stock) == ['rock'], 'one mineral after another')


@scenario.step(2.5)
def unloaded() -> None:
    base = scenario.base
    check(scenario.player.miner.ore == {}, 'the cargo is empty')
    check(base.depot.stock == pytest.approx(CARGO), 'all in the depot')
    check(not base.unloading and not base.can_unload, 'unloading is over')
    scenario.player.miner.ore.update({'ice': 40.})


@scenario.step(.3)
def unloads_again() -> None:
    scenario.press(scenario.base.ids.unload_button)


@scenario.step(.5)
def takes_off() -> None:
    remembered.append(scenario.hold_towards(scenario.away_from_earth()))


@scenario.step(.8)
def stopped() -> None:
    remembered[0].touch_up()
    base = scenario.base
    ice = scenario.player.miner.ore.get('ice', 0.)
    check(not base.unloading, 'taking off stops unloading')
    check(0 < ice < 40, f'the rest stays in the cargo: {ice:.1f}')
    check(base.ids.depot.opacity == 0, 'the depot hides once flying')
    base.depot.stock.clear()
    base.depot.stock['iron'] = DEPOT_CAPACITY - 5.
    scenario.player.restart(scenario.player.design)
    scenario.player.miner.ore.clear()
    scenario.player.miner.ore['iron'] = 20.


@scenario.step(.3)
def fills_the_depot() -> None:
    base = scenario.base
    scenario.press(base.ids.unload_button)


@scenario.step(1.)
def as_far_as_it_goes() -> None:
    base = scenario.base
    stock = base.depot.stock
    check(stock == {'iron': DEPOT_CAPACITY}, f'as far as it goes: {stock}')
    check(scenario.player.miner.ore == {'iron': 15.},
          f'the rest stays: {scenario.player.miner.ore}')
    button = base.ids.unload_button
    check(button.text == 'Entrepôt plein', f'told: {button.text}')
    check(button.disabled, 'nothing more goes in')


remembered: list[Any] = []

scenario.run()
