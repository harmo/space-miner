""" The Icare station, orbiting the first planet: a wide ship coming from
the side away from its port docks all the same, builds it, then is
sheltered there from the heat of the sun, and sells it the ore of flare
ejecta, dearer than anywhere """

import math
from typing import Any

from app.logic.base.market import ore_price
from app.logic.ship.config import LANDING_DURATION
from app.logic.ship.shipyard import Design

from .harness import Scenario

scenario = Scenario('icare')
check = scenario.check
remembered: dict[str, Any] = {}
played = scenario.record_sounds()


def icare() -> Any:
    return next(o for o in scenario.game.outposts if o.key == 'icare')


def view() -> Any:
    return scenario.game.ids.outpost


@scenario.step(1.)
def flies_to_the_station() -> None:
    station, system = icare(), scenario.game.system
    check(station.body.orbit.parent is system.planets[0],
          'around the first planet')
    scenario.player.restart(Design('hauler', {
        'left_front': 'container', 'left_back': 'container',
        'right_front': 'container', 'right_back': 'container',
    }))
    x, y = station.body.pos
    away = station.direction + math.pi
    scenario.put_ship(
        (x + math.cos(away) * 150, y + math.sin(away) * 150),
        station.body.velocity, angle=away,
    )


@scenario.step(.3)
def docks() -> None:
    scenario.screenshot('beacon')
    button = scenario.game.ids.land_button
    check(button.text == "S'amarrer", f'the shortcut docks: {button.text}')
    check(scenario.player.shortcut == 'ready', 'close enough')
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def is_docked() -> None:
    check(view().docked, 'docked at its port')
    scenario.grant_concessions()
    parking, station = scenario.player.parking, icare()
    check(abs(parking.direction - station.direction) < 1e-6,
          'gone around the station')
    check('dock' in played and 'touchdown' not in played,
          f'heard docking: {played}')
    ore = scenario.player.miner.ore
    stages = icare().construction.site.stages
    ore.update({name: float(units) for name, units in stages[0].materials})
    icare().deliver(ore)


@scenario.step(.3)
def builds_its_frame() -> None:
    scenario.screenshot('frame')
    ore = scenario.player.miner.ore
    for stage in icare().construction.site.stages[1:]:
        ore.update({name: float(units) for name, units in stage.materials})
        icare().deliver(ore)
    check(icare().construction.built == 3, 'built up to its trading post')
    scenario.player.heat.level = .7


@scenario.step(1.)
def shelters_the_ship() -> None:
    heat = scenario.player.heat.level
    check(heat < .5, f'the hull cools down, docked: {heat:.2f}')
    scenario.screenshot('station')
    icare().post.depot.stock['stellarium'] = 2.
    scenario.press(view().ids.market_button)


@scenario.step(.3)
def buys_ejecta_dearer() -> None:
    market = view().ids.market
    price = market.price('stellarium')
    check(price > ore_price('stellarium') * 1.5,
          f'stellarium is dearer here: {price}')
    check(market.price('iron') == ore_price('iron'), 'iron is not')
    check(not view().has_missions, 'and no missions')


scenario.run()
