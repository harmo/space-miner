""" Cérès: a big asteroid in the middle of the belt around the sun, where
the ship lands on a small pad. Landed there out of fuel before anything
is built, it calls for help. Built up to its refinery, it crushes the
rock of its depot there, with no missions. """

import math
from typing import Any

from app.logic.ship.config import LANDING_DURATION
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
def has_no_missions() -> None:
    check(view().trading and not view().contracting,
          'a market, but no missions')
    scenario.screenshot('refinery')
    ceres().post.depot.stock['rock'] = 40.
    scenario.press(view().ids.market_button)


@scenario.step(.3)
def crushes_rock_there() -> None:
    market = view().ids.market
    check(market.refinery, 'the market has its refinery')
    scenario.press(scenario.button(market, 'Concasser la roche'))


@scenario.step(2.)
def into_other_ore() -> None:
    stock = ceres().post.depot.stock
    check(stock.get('rock', 0.) < 40. and len(stock) > 1,
          f'the rock is crushed there: {stock}')
    check(not scenario.base.depot.stock, 'not on the Earth')


scenario.run()
