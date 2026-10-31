""" The refinery: rock of the depot crushed a bit at a time from the
market, giving other ore now and then, until none is left """

from app.logic.base.config import CRUSH_RATE

from .harness import Scenario

scenario = Scenario('refinery')
check = scenario.check
ROCK = 40.


def market() -> object:
    return scenario.base.ids.market


@scenario.step(1.)
def opens_the_market() -> None:
    base = scenario.base
    base.depot.stock.update({'rock': ROCK})
    scenario.press(base.ids.market_button)


@scenario.step(.3)
def crushes_the_rock() -> None:
    scenario.press(scenario.button(market(), 'Concasser la roche'))


@scenario.step(2.)
def bit_by_bit() -> None:
    base = scenario.base
    rock = base.depot.stock.get('rock', 0.)
    check(ROCK - 3 * CRUSH_RATE < rock < ROCK - CRUSH_RATE,
          f'crushed a bit at a time: {rock:.1f} left')
    check(base.crushing, 'the refinery works')
    machine = scenario.game.soundtrack.machine
    check(machine.name == 'crushing' and machine.playing, 'heard')
    button = scenario.button(market(), 'Concassage…')
    check(button.disabled, 'once')
    scenario.screenshot('crushing')


@scenario.step(ROCK / CRUSH_RATE)
def until_none_is_left() -> None:
    base = scenario.base
    stock = base.depot.stock
    check('rock' not in stock, f'the rock is crushed: {stock}')
    check(sum(stock.values()) > 0, f'into other ore: {stock}')
    check(not base.crushing, 'the refinery stops')
    check(scenario.game.soundtrack.machine.name is None, 'falling silent')
    button = scenario.button(market(), 'Concasser la roche')
    check(button.disabled, 'with no rock left')


scenario.run()
