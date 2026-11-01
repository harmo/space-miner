""" Base Ares, on Mars: built stage after stage up to its mine, which digs
metals and dust into its depot, the ore being loaded back as nothing is
traded there """

import math
from typing import Any

from app.logic.ship.config import LANDING_DURATION

from .harness import Scenario

scenario = Scenario('ares')
check = scenario.check


def ares() -> Any:
    return next(o for o in scenario.game.outposts if o.key == 'ares')


def view() -> Any:
    return scenario.game.ids.outpost


@scenario.step(1.)
def flies_to_mars() -> None:
    outpost = ares()
    check(outpost.body is scenario.game.system.mars, 'on Mars')
    x, y = outpost.pos
    direction = outpost.direction
    scenario.put_ship(
        (x + math.cos(direction) * 120, y + math.sin(direction) * 120),
        outpost.body.velocity, angle=direction,
    )


@scenario.step(.3)
def lands_on_its_pad() -> None:
    check(scenario.player.shortcut == 'ready', 'its pad is there')
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def builds_it() -> None:
    check(view().docked, 'served there')
    outpost = ares()
    for stage in outpost.construction.site.stages:
        outpost.deliver({name: float(n) for name, n in stage.materials})
    check(outpost.construction.stage is None, 'all of it built')
    outpost.post.mine.dug = 40.5


@scenario.step(.3)
def digs_metals_and_dust() -> None:
    stock = ares().post.depot.stock
    check(sum(stock.values()) == 40., f'in its depot: {stock}')
    check(set(stock) <= {'iron', 'copper', 'regolith'}, f'{stock}')
    check(not view().has_market and not view().has_missions, 'nothing more')
    button = view().ids.market_button
    check(button.text == 'Entrepôt', f'its depot alone: {button.text}')
    scenario.screenshot('mine')
    scenario.press(button)


@scenario.step(.3)
def loads_it_back() -> None:
    market = view().ids.market
    check(not market.selling, 'nothing to sell')
    scenario.press(scenario.button(market, 'Charger'))
    check(sum(scenario.player.miner.ore.values()) > 0, 'into the cargo')


scenario.run()
