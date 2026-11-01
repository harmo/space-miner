""" Shuttles: the Earth has none, only a pad to take them. The dock of an
outpost sends the ore chosen to another depot once it can leave full, and
comes back, flying round every body, seen on the map with what it carries.
Posts without a depot are not offered. """

import math
from typing import Any

from app.logic.base.config import SHUTTLE_ARRIVAL
from app.logic.base.mine import Vein
from app.logic.base.shuttle_flight import fly
from app.logic.ship.config import LANDING_DURATION

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


def view() -> Any:
    return scenario.game.ids.outpost


def shuttle() -> Any:
    return outpost('ares').post.shuttle


def panel() -> Any:
    return view().ids.shuttles


def choices(box: str) -> dict[str, Any]:
    return {b.key: b for b in panel().ids[box].children}


@scenario.step(1.)
def opens_the_market() -> None:
    scenario.screenshot('earth')
    check(quay('earth').berths, 'a pad on the Earth')
    scenario.press(scenario.base.ids.market_button)


@scenario.step(.3)
def has_no_shuttle_on_the_earth() -> None:
    market = scenario.base.ids.market
    check(not market.shuttles, 'the Earth only takes them')
    scenario.press(scenario.button(market, 'Fermer'))
    outpost_there = outpost('ares')
    x, y = outpost_there.pos
    direction = outpost_there.direction
    scenario.put_ship(
        (x + math.cos(direction) * 120, y + math.sin(direction) * 120),
        outpost_there.body.velocity, angle=direction,
    )


@scenario.step(.3)
def lands_at_ares() -> None:
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def builds_its_dock() -> None:
    check(view().docked, 'landed at Ares')
    scenario.grant_concessions()
    ares = outpost('ares')
    for stage in ares.construction.site.stages:
        ares.deliver({name: float(n) for name, n in stage.materials})
    # Only what the scenario puts there
    ares.post.mine.vein = Vein(rate=0.)
    ares.post.depot.stock.clear()
    ares.post.depot.stock.update({'iron': 30., 'gold': 5.})


@scenario.step(.3)
def opens_its_depot() -> None:
    scenario.press(view().ids.market_button)


@scenario.step(.3)
def opens_the_dock() -> None:
    market = view().ids.market
    check(market.shuttles, 'a depot elsewhere: a shuttle')
    scenario.press(scenario.button(market, 'Navette'))


@scenario.step(.3)
def chooses_where_and_what() -> None:
    check(view().panel == 'shuttles', 'the dock opens')
    places = choices('places')
    check(set(places) == {'earth'}, f'only depots: {set(places)}')
    check(set(choices('minerals')) == {'iron', 'gold'}, 'what the depot has')
    scenario.press(places['earth'])


@scenario.step(.2)
def no_route_without_ore() -> None:
    check(shuttle().route is None, 'nothing chosen yet')
    scenario.press(choices('minerals')['iron'])


@scenario.step(.3)
def waits_to_leave_full() -> None:
    scenario.screenshot('panel')
    route = shuttle().route
    check(route is not None and route.destination == 'earth', f'{route}')
    check(shuttle().leg == 'waiting', f'not full yet: {shuttle().leg}')
    stock = outpost('ares').post.depot.stock
    check(stock == {'iron': 30., 'gold': 5.}, 'all of it in the depot')
    check('30 / 100' in panel().status, f'told: {panel().status}')
    stock['iron'] = 100.


@scenario.step(.3)
def leaves() -> None:
    check(shuttle().leg == 'out', f'on its way: {shuttle().leg}')
    check(shuttle().load == {'iron': 100.}, f'carrying: {shuttle().load}')
    check(outpost('ares').post.depot.stock == {'gold': 5.}, 'the rest stays')
    check('En route' in panel().status, f'told: {panel().status}')
    # In front of the ship, to be seen
    x, y = scenario.player.anchor
    sun = scenario.game.system.sun.pos
    shuttle().offset = x + 120 - sun[0], y + 200 - sun[1]


@scenario.step(.4)
def flies() -> None:
    scenario.screenshot('flying')
    # Not to wait for the whole trip
    x, y = quay('earth').spot
    sun = scenario.game.system.sun.pos
    shuttle().offset = x + 40 - sun[0], y - sun[1]


@scenario.step(.6)
def delivers() -> None:
    stock = scenario.base.depot.stock
    check(stock == {'iron': 100.}, f'in the depot of the Earth: {stock}')
    check(shuttle().leg == 'back', f'coming back: {shuttle().leg}')
    check('retour' in panel().status, f'told: {panel().status}')
    scenario.press(scenario.button(panel(), 'Fermer'))
    scenario.press(scenario.game.ids.map_button)


@scenario.step(.3)
def shows_on_the_map() -> None:
    view = scenario.game.ids.map.ids.view
    marks = view.shown.shuttles
    check(len(marks) == 1, f'one on its way: {marks}')
    check(marks[0].way == 'Terre vers Base Ares',
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
