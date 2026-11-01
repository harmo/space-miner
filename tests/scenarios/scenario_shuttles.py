""" Shuttles: from the market of the Earth, a dock sends the ore chosen to
an outpost with a depot once it can leave full, and comes back, flying
round every body, seen on the map with what it carries. Posts without a
depot are not offered. """

import math
from typing import Any

from app.logic.base.config import SHUTTLE_ARRIVAL
from app.logic.base.shuttle_flight import fly

from .harness import Scenario

scenario = Scenario('shuttles')
check = scenario.check
STEP = 20.                    # pixels, checking each way on
STEPS = 4000
remembered: dict[str, Any] = {}


def outpost(key: str) -> Any:
    return next(o for o in scenario.game.outposts if o.key == key)


def quay(key: str) -> Any:
    return next(q for q in scenario.game.quays if q.key == key)


def panel() -> Any:
    return scenario.base.ids.shuttles


def choices(box: str) -> dict[str, Any]:
    return {b.key: b for b in panel().ids[box].children}


@scenario.step(1.)
def opens_the_market() -> None:
    scenario.screenshot('dock')
    scenario.press(scenario.base.ids.market_button)


@scenario.step(.3)
def has_nowhere_to_send_to() -> None:
    market = scenario.base.ids.market
    check(not market.shuttles, 'no depot elsewhere: no shuttles')
    scenario.press(scenario.button(market, 'Fermer'))


@scenario.step(.3)
def builds_a_depot_at_ares() -> None:
    scenario.grant_concessions()
    ares = outpost('ares')
    for stage in ares.construction.site.stages[:2]:
        ares.deliver({name: float(n) for name, n in stage.materials})
    scenario.base.depot.stock.update({'iron': 30., 'gold': 5.})
    scenario.press(scenario.base.ids.market_button)


@scenario.step(.3)
def opens_the_dock() -> None:
    market = scenario.base.ids.market
    check(market.shuttles, 'a depot elsewhere: shuttles')
    scenario.press(scenario.button(market, 'Navette'))


@scenario.step(.3)
def chooses_where_and_what() -> None:
    check(scenario.base.panel == 'shuttles', 'the dock opens')
    places = choices('places')
    check(set(places) == {'ares'}, f'only depots: {set(places)}')
    check(set(choices('minerals')) == {'iron', 'gold'}, 'what the depot has')
    scenario.press(places['ares'])


@scenario.step(.2)
def no_route_without_ore() -> None:
    check(scenario.base.post.shuttle.route is None, 'nothing chosen yet')
    scenario.press(choices('minerals')['iron'])


@scenario.step(.3)
def waits_to_leave_full() -> None:
    scenario.screenshot('panel')
    shuttle = scenario.base.post.shuttle
    route = shuttle.route
    check(route is not None and route.destination == 'ares', f'{route}')
    check(shuttle.leg == 'waiting', f'not full yet: {shuttle.leg}')
    check(scenario.base.depot.stock == {'iron': 30., 'gold': 5.},
          'all of it staying in the depot')
    check('30 / 100' in panel().status, f'told: {panel().status}')
    scenario.base.depot.stock['iron'] = 100.


@scenario.step(.3)
def leaves() -> None:
    shuttle = scenario.base.post.shuttle
    check(shuttle.leg == 'out', f'on its way: {shuttle.leg}')
    check(shuttle.load == {'iron': 100.}, f'carrying: {shuttle.load}')
    check(scenario.base.depot.stock == {'gold': 5.}, 'the rest stays')
    check('En route' in panel().status, f'told: {panel().status}')
    # In front of the ship, to be seen
    x, y = scenario.player.anchor
    sun = scenario.game.system.sun.pos
    shuttle.offset = x + 120 - sun[0], y - 200 - sun[1]


@scenario.step(.4)
def flies() -> None:
    scenario.screenshot('flying')
    # Not to wait for the whole trip
    x, y = quay('ares').spot
    sun = scenario.game.system.sun.pos
    scenario.base.post.shuttle.offset = x + 40 - sun[0], y - sun[1]


@scenario.step(.6)
def delivers() -> None:
    stock = outpost('ares').post.depot.stock
    check(stock == {'iron': 100.}, f'in the depot of Ares: {stock}')
    shuttle = scenario.base.post.shuttle
    check(shuttle.leg == 'back', f'coming back: {shuttle.leg}')
    check('retour' in panel().status, f'told: {panel().status}')
    scenario.press(scenario.button(panel(), 'Fermer'))
    scenario.press(scenario.game.ids.map_button)


@scenario.step(.3)
def shows_on_the_map() -> None:
    view = scenario.game.ids.map.ids.view
    marks = view.shown.shuttles
    check(len(marks) == 1, f'one on its way: {marks}')
    check(marks[0].way == 'Base Ares vers Terre',
          f'told: {marks[0].way}')
    check(marks[0].carried == 'À vide', f'told: {marks[0].carried}')
    scenario.press(view, view.chart.place(marks[0].pos))


@scenario.step(.3)
def tells_what_it_carries() -> None:
    view = scenario.game.ids.map.ids.view
    check(view.picked is view.shown.shuttles[0], 'tapping it picks it')
    scenario.screenshot('map')
    scenario.game.map_open = False


@scenario.step(.3)
def never_goes_through_a_body() -> None:
    game = scenario.game
    quays = game.quays
    obstacles = game.airspace.obstacles
    for start in quays:
        for end in quays:
            if start is end:
                continue
            pos = start.spot
            for _ in range(STEPS):
                pos, _angle = fly(pos, end.spot, obstacles, STEP)
                check(all(math.dist(pos, o.pos) >= o.reach - 1
                          for o in obstacles),
                      f'{start.key} to {end.key} goes through a body')
                if math.dist(pos, end.spot) < STEP + SHUTTLE_ARRIVAL:
                    break
            else:
                check(False, f'{start.key} never gets to {end.key}')
    scenario.grant_concessions()
    for outpost_there in game.outposts:
        for stage in outpost_there.construction.site.stages:
            outpost_there.deliver({n: float(u) for n, u in stage.materials})
    show_dock('ares')


def show_dock(key: str) -> None:
    there = quay(key)
    x, y = there.spot
    away = math.atan2(y - there.body.pos[1], x - there.body.pos[0])
    scenario.put_ship(
        (x + math.cos(away) * 160, y + math.sin(away) * 160),
        there.body.velocity, angle=away,
    )


@scenario.step(.3)
def has_a_dock_at_ares() -> None:
    check(quay('ares').docks, 'built')
    scenario.screenshot('dock-ares')
    show_dock('icare')


@scenario.step(.3)
def has_a_dock_at_icare() -> None:
    scenario.screenshot('dock-icare')
    show_dock('ceres')


@scenario.step(.3)
def has_a_dock_at_ceres() -> None:
    scenario.screenshot('dock-ceres')


scenario.run()
