""" Outposts: the site of the Frontier on the farthest planet, where the
ship lands on its pad. Ore delivered from the cargo builds it stage after
stage: its foundations fill the tank, its habitat keeps ore unloaded in a
depot of its own, from where it loads back, all of it saved, its trading
post buys ore dearer than the Earth and gives missions of its own, making
a reputation of its own, and its mine digs ore into its depot. """

import json
import math
import os
from typing import Any

from app.logic.base.market import ore_price
from app.logic.ship.config import LANDING_DURATION

from .harness import Scenario

scenario = Scenario('outposts')
check = scenario.check
remembered: dict[str, Any] = {}
played = scenario.record_sounds()


def frontier() -> Any:
    return scenario.game.outposts[0]


def view() -> Any:
    return scenario.game.ids.outpost


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
    check(view().docked, 'served on the pad')
    check(not scenario.base.docked, 'not at the base on the Earth')
    check(view().ids.site_button.opacity == 1, 'its site can be opened')
    player.miner.ore.update({'rock': 130., 'iron': 10.})
    player.tank.level = 10.
    scenario.base.wallet.credits = 1000
    scenario.press(view().ids.site_button)


@scenario.step(.3)
def tells_what_the_foundations_need() -> None:
    panel = view().ids.site
    check(view().panel == 'site', 'the site opens')
    check('Fondations' in panel.stage, f'its first stage: {panel.stage}')
    check(panel.can_deliver, 'the cargo holds what it needs')
    scenario.screenshot('panel')
    scenario.press(scenario.button(panel, 'Livrer'))


@scenario.step(.3)
def builds_the_foundations() -> None:
    panel, player = view().ids.site, scenario.player
    check(frontier().construction.built == 1, 'the foundations are built')
    check(panel.news == 'Fondations construit', f'as told: {panel.news}')
    # Then the tank filled, by the foundations
    check(played[-2:] == ['built', 'refuel'], f'and heard: {played}')
    check('Habitat' in panel.stage, f'the habitat comes next: {panel.stage}')
    check(player.miner.ore == {'rock': 10., 'iron': 10.},
          f'the rest is kept: {player.miner.ore}')
    check(player.tank.share == 1., 'the outpost fills the tank')
    scenario.press(scenario.button(panel, 'Livrer'))


@scenario.step(.3)
def delivers_part_of_the_habitat() -> None:
    construction = frontier().construction
    check(construction.built == 1, 'not enough for the habitat')
    check(construction.delivered == {'rock': 10, 'iron': 10},
          f'but delivered: {construction.delivered}')
    check(played[-1:] == ['deliver'], f'as heard: {played}')
    scenario.player.miner.ore.update({'rock': 150., 'iron': 30., 'gold': 3.})
    view().open('site')                 # showing the new cargo


@scenario.step(.2)
def delivers_the_rest() -> None:
    scenario.press(scenario.button(view().ids.site, 'Livrer'))


@scenario.step(.3)
def builds_the_habitat() -> None:
    check(frontier().construction.built == 2, 'the habitat is built')
    check(frontier().post.services.depot, 'with a depot')
    scenario.screenshot('habitat')
    scenario.press(scenario.button(view().ids.site, 'Fermer'))


@scenario.step(.3)
def unloads_there() -> None:
    check(view().has_depot and view().can_unload, 'the cargo can unload')
    scenario.press(view().ids.unload_button)


@scenario.step(1.)
def into_its_own_depot() -> None:
    stock = frontier().post.depot.stock
    check(stock == {'gold': 3.}, f'the gold is unloaded there: {stock}')
    check('gold' not in scenario.base.depot.stock, 'not on the Earth')
    scenario.screenshot('depot')
    button = view().ids.market_button
    check(button.text == 'Entrepôt', f'no market yet: {button.text}')
    scenario.press(button)


@scenario.step(.3)
def opens_its_depot_alone() -> None:
    market = view().ids.market
    check(view().panel == 'market' and not market.selling, 'nothing to sell')
    check(market.ids.rows.children[0].selling is False, 'nor any price')
    scenario.screenshot('depot_panel')
    scenario.press(scenario.button(market, 'Charger'))


@scenario.step(.3)
def loads_it_back() -> None:
    check(scenario.player.miner.ore == {'gold': 3.}, 'back in the cargo')
    check(not frontier().post.depot.stock, 'out of the depot')
    market = view().ids.market
    check(market.empty and not market.ids.rows.children, 'its row is gone')
    scenario.press(scenario.button(market, 'Fermer'))


@scenario.step(.3)
def unloads_it_again() -> None:
    scenario.press(view().ids.unload_button)


@scenario.step(1.)
def is_back_in_the_depot() -> None:
    stock = frontier().post.depot.stock
    check(stock == {'gold': 3.}, f'unloaded again: {stock}')
    scenario.game.save()


@scenario.step(.1)
def is_saved() -> None:
    path = os.path.join(scenario.data, 'save.json')
    with open(path, encoding='utf-8') as file:
        saved = json.load(file)['outposts']['frontier']
    check(saved['built'] == 2 and saved['stock'] == {'gold': 3.},
          f'saved as built: {saved}')
    scenario.player.miner.ore.update(
        {'rock': 200., 'iron': 60., 'copper': 30.}
    )
    view().open('site')


@scenario.step(.2)
def builds_the_trading_post() -> None:
    scenario.press(scenario.button(view().ids.site, 'Livrer'))


@scenario.step(.3)
def trades() -> None:
    check(frontier().construction.built == 3, 'the trading post is built')
    scenario.press(scenario.button(view().ids.site, 'Fermer'))


@scenario.step(.3)
def opens_its_market() -> None:
    check(view().has_market, 'it has a market and missions')
    button = view().ids.market_button
    check(button.text == 'Marché', f'as told: {button.text}')
    remembered['credits'] = scenario.base.wallet.credits
    scenario.press(view().ids.market_button)


@scenario.step(.3)
def sells_dearer_than_the_earth() -> None:
    market = view().ids.market
    check(market.selling, 'selling now')
    price = market.price('gold')
    check(price > ore_price('gold'), f'gold is dearer: {price}')
    market.sell('gold')
    paid = scenario.base.wallet.credits - remembered['credits']
    check(paid == 3 * price, f'paid {paid}')
    scenario.screenshot('market')
    scenario.press(scenario.button(market, 'Fermer'))


@scenario.step(.3)
def opens_its_missions() -> None:
    scenario.press(view().ids.missions_button)


@scenario.step(.3)
def takes_a_mission_of_its_own() -> None:
    board = frontier().board
    mission = board.offers[0]
    clientele = frontier().construction.site.trade.clientele
    check(mission.client in clientele.clients,
          f'from a local client: {mission.client}')
    check(mission not in scenario.base.board.offers, 'not of the Earth')
    board.accept(mission)
    frontier().post.depot.stock.update(
        {name: float(units) for name, units in mission.wanted.items()}
    )
    remembered['mission'] = mission
    view().ids.missions.refresh()
    scenario.screenshot('missions')


@scenario.step(.3)
def validates_it_there() -> None:
    mission = remembered['mission']
    tracker = scenario.game.ids.tracker
    check(tracker.shown, 'the mission is tracked, wherever it was taken')
    scanner = scenario.game.ids.scanner
    scanner.for_missions()
    check(scenario.player.looked_for == set(mission.wanted),
          'and looked for by the scanner')
    earth = scenario.base.board.validated
    card = next(
        card for card in view().ids.missions.ids.active.children
        if card.mission is mission
    )
    scenario.press(scenario.button(card, 'Valider'))
    check(frontier().board.validated == 1, 'making its reputation')
    check(scenario.base.board.validated == earth, 'not that of the Earth')
    scenario.press(scenario.button(view().ids.missions, 'Fermer'))
    check(frontier().construction.stage.name == 'Mine', 'a mine comes next')
    frontier().post.depot.stock.clear()
    frontier().deliver(dict(
        (name, float(units))
        for name, units in frontier().construction.stage.materials
    ))
    check(frontier().post.services.mine, 'the mine is built')


@scenario.step(.3)
def has_its_mine_built() -> None:
    check(not view().building, 'nothing left to build')
    check(not frontier().post.depot.stock, 'nothing dug yet')
    frontier().post.mine.dug = 3.5


@scenario.step(.3)
def digs_on_its_own() -> None:
    stock = frontier().post.depot.stock
    check(sum(stock.values()) == 3., f'ore in its depot: {stock}')
    check(set(stock) <= {'helium3', 'ice'}, f'helium and ice: {stock}')
    scenario.screenshot('mine')


scenario.run()
