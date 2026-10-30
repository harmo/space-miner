""" Outposts: the site of the Frontier on the farthest planet, where the
ship lands on its pad. Ore delivered from the cargo builds it stage after
stage: its foundations fill the tank, its habitat keeps ore unloaded in a
depot of its own, all of it saved. """

import json
import math
import os
from typing import Any

from app.logic.ship.config import LANDING_DURATION

from .harness import Scenario

scenario = Scenario('outposts')
check = scenario.check
remembered: dict[str, Any] = {}


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
    scenario.player.miner.ore.update({'rock': 150., 'iron': 30., 'gold': 3.})
    view().open()                       # showing the new cargo


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
    scenario.game.save()


@scenario.step(.1)
def is_saved() -> None:
    path = os.path.join(scenario.data, 'save.json')
    with open(path, encoding='utf-8') as file:
        saved = json.load(file)['outposts']['frontier']
    check(saved['built'] == 2 and saved['stock'] == {'gold': 3.},
          f'saved as built: {saved}')


scenario.run()
