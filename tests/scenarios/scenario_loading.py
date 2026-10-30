""" Loading ore back from the market into the ship, as far as it fits,
which stops unloading """

from typing import Any

from .harness import Scenario

scenario = Scenario('loading')
check = scenario.check


def market() -> Any:
    return scenario.base.ids.market


def row(mineral: str) -> Any:
    return next(
        widget for widget in market().ids.rows.children
        if widget.mineral == mineral
    )


@scenario.step(1.)
def opens_the_market() -> None:
    base = scenario.base
    base.depot.stock.update({'iron': 50., 'gold': 3.})
    scenario.press(base.ids.market_button)


@scenario.step(.3)
def loads_as_far_as_it_fits() -> None:
    check(row('iron').can_load, 'the cargo is empty')
    scenario.screenshot('market')
    scenario.press(scenario.button(row('iron'), 'Charger'))


@scenario.step(.3)
def fills_the_cargo() -> None:
    player, stock = scenario.player, scenario.base.depot.stock
    capacity = player.miner.capacity
    check(player.miner.ore == {'iron': capacity},
          f'as much as fits: {player.miner.ore}')
    check(stock['iron'] == 50. - capacity, f'taken from the depot: {stock}')
    check(not row('gold').can_load, 'the cargo is full')
    scenario.press(scenario.button(market(), 'Fermer'))


@scenario.step(.3)
def unloads() -> None:
    scenario.press(scenario.base.ids.unload_button)


@scenario.step(.3)
def loads_while_unloading() -> None:
    check(scenario.base.unloading, 'unloading')
    scenario.press(scenario.base.ids.market_button)


@scenario.step(.3)
def stops_unloading() -> None:
    scenario.press(scenario.button(row('gold'), 'Charger'))


@scenario.step(.3)
def keeps_what_it_loaded() -> None:
    check(not scenario.base.unloading, 'unloading stops')
    ore = scenario.player.miner.ore
    check(ore.get('gold') == 3., f'the gold stays on board: {ore}')


scenario.run()
