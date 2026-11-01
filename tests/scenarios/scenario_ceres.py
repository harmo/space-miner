""" Cérès: a big asteroid in the middle of the belt around the sun, in a
cloud of asteroids of its own which is always full, where the ship lands
on a small pad. Landed there out of fuel before anything is built, it
calls for help. Built up to its refinery, faster and richer than the one
of the Earth, it crushes the rock of its depot there, and takes orders of
common ore from building sites. """

import math
from typing import Any

from app.logic.base.config import CERES_CRUSH_RATE
from app.logic.ship.config import LANDING_DURATION
from app.logic.world.config import CERES_BELT_ASTEROIDS, CERES_REGROW_TIME
from app.logic.world.layout import sun_belt_orbit

from .harness import Scenario

scenario = Scenario('ceres')
check = scenario.check
remembered: dict[str, Any] = {}


def ceres() -> Any:
    return next(o for o in scenario.game.outposts if o.key == 'ceres')


def view() -> Any:
    return scenario.game.ids.outpost


@scenario.step(1.)
def flies_to_ceres() -> None:
    outpost, system = ceres(), scenario.game.system
    distance = math.dist(outpost.body.pos, system.sun.pos)
    belt = sun_belt_orbit(system.orbits)
    check(abs(distance - belt) < 1, f'in the belt around the sun: {distance}')
    check(outpost.body in system.attractors, 'pulling the ship')
    cloud = system.belts[-1]
    check(len(cloud) == CERES_BELT_ASTEROIDS, f'its cloud: {len(cloud)}')
    check(all(a.orbit.parent is outpost.body for a in cloud),
          'turning around it')
    for asteroid in cloud[:3]:
        system.remove(asteroid)
    # Below it, away from its pad
    x, y = outpost.body.pos
    scenario.put_ship((x, y - outpost.body.radius - 120),
                      outpost.body.velocity)


@scenario.step(4 * CERES_REGROW_TIME / CERES_BELT_ASTEROIDS)
def is_aside_from_the_pad() -> None:
    cloud = scenario.game.system.belts[-1]
    check(len(cloud) == CERES_BELT_ASTEROIDS, f'grown back: {len(cloud)}')
    button = scenario.game.ids.land_button
    check(button.text == 'Hors de la plateforme', f'told: {button.text}')
    above_the_pad()


def above_the_pad() -> None:
    outpost = ceres()
    x, y = outpost.pos
    direction = outpost.direction
    scenario.put_ship(
        (x + math.cos(direction) * 120, y + math.sin(direction) * 120),
        outpost.body.velocity, angle=direction,
    )


@scenario.step(.3)
def lands_there() -> None:
    scenario.screenshot('site')
    shortcut = scenario.player.shortcut
    check(shortcut == 'ready', f'the landing shortcut is ready: {shortcut}')
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def runs_dry_there() -> None:
    check(view().docked, 'landed on the bare site')
    scenario.player.tank.level = 0.
    scenario.player.miner.ore['iron'] = 5.
    scenario.base.wallet.credits = 1000


@scenario.step(.3)
def calls_for_help() -> None:
    button = scenario.game.ids.distress_button
    check(scenario.base.stranded and button.opacity == 1,
          'stranded there, help can be called')
    scenario.press(button)


@scenario.step(.5)
def is_towed_home() -> None:
    check(scenario.base.docked, 'back on the Earth')
    check(scenario.player.miner.ore == {'iron': 5.}, 'with its cargo')
    scenario.player.miner.ore.clear()
    above_the_pad()


@scenario.step(.3)
def lands_there_again() -> None:
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def builds_it() -> None:
    check(view().docked, 'served on its small pad')
    ore = scenario.player.miner.ore
    for stage in ceres().construction.site.stages:
        ore.update({name: float(units) for name, units in stage.materials})
        ceres().deliver(ore)
    check(ceres().construction.built == 3, 'built up to its refinery')


@scenario.step(.3)
def orders_ore_by_the_shipload() -> None:
    check(view().has_market and view().has_missions, 'a market and missions')
    board = ceres().board
    orders = dict(ceres().construction.site.trade.clientele.orders)
    check(all(set(m.wanted) <= set(orders) for m in board.offers),
          f'of common ore: {board.offers}')
    mission = board.offers[0]
    board.accept(mission)
    remembered['mission'] = mission
    scenario.base.wallet.credits = 0
    ceres().post.depot.stock.update(
        {name: float(units) for name, units in mission.wanted.items()}
    )
    scenario.press(view().ids.missions_button)


@scenario.step(.3)
def validates_an_order() -> None:
    mission = remembered['mission']
    missions = view().ids.missions
    scenario.screenshot('orders')
    card = next(
        card for card in missions.ids.active.children
        if card.mission is mission
    )
    scenario.press(scenario.button(card, 'Valider'))
    wallet = scenario.base.wallet
    check(wallet.credits == mission.reward, f'paid: {wallet.credits}')
    check(not ceres().post.depot.stock, 'the ore goes')
    scenario.press(scenario.button(missions, 'Fermer'))


@scenario.step(.3)
def has_its_market_back() -> None:
    scenario.screenshot('refinery')
    scenario.player.miner.ore['rock'] = 40.


@scenario.step(.2)
def unloads_there() -> None:
    scenario.press(view().ids.unload_button)


@scenario.step(.5)
def is_heard_unloading() -> None:
    machine = scenario.game.soundtrack.machine
    check(machine.name == 'unloading', f'unloading there: {machine.name}')


@scenario.step(3.)
def opens_the_market() -> None:
    check(ceres().post.depot.stock.get('rock') == 40., 'all of it unloaded')
    scenario.press(view().ids.market_button)


@scenario.step(.3)
def crushes_rock_there() -> None:
    market = view().ids.market
    check(market.refinery, 'the market has its refinery')
    check('rubis' in market.refinery_told, 'telling how rich it is')
    scenario.screenshot('market')
    scenario.press(scenario.button(market, 'Concasser la roche'))


@scenario.step(2.)
def into_other_ore() -> None:
    stock = ceres().post.depot.stock
    check(stock.get('rock', 0.) < 40. and len(stock) > 1,
          f'the rock is crushed there: {stock}')
    check(not scenario.base.depot.stock, 'not on the Earth')
    machine = scenario.game.soundtrack.machine
    check(machine.name == 'crushing', f'heard: {machine.name}')
    check(view().ids.market.crushing, 'as the market shows')


@scenario.step(40. / CERES_CRUSH_RATE)
def until_it_is_over() -> None:
    check(not view().ids.market.crushing, 'the market shows it is over')
    check(scenario.game.soundtrack.machine.name is None, 'falling silent')


scenario.run()
