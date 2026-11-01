""" Shuttles: from the market of the Earth, a dock sends the ore chosen to
an outpost with a depot, and comes back. Posts without a depot are not
offered, and those with a dock of their own can send ore too. """

from typing import Any

from app.logic.base.config import SHUTTLE_MIN_TRIP

from .harness import Scenario

scenario = Scenario('shuttles')
check = scenario.check
remembered: dict[str, Any] = {}


def outpost(key: str) -> Any:
    return next(o for o in scenario.game.outposts if o.key == key)


def panel() -> Any:
    return scenario.base.ids.shuttles


def choices(box: str) -> dict[str, Any]:
    return {b.key: b for b in panel().ids[box].children}


@scenario.step(1.)
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
    scenario.press(scenario.button(market, 'Navettes'))


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
def leaves() -> None:
    scenario.screenshot('panel')
    shuttle = scenario.base.post.shuttle
    route = shuttle.route
    check(route is not None and route.destination == 'ares', f'{route}')
    check(shuttle.leg == 'out', f'on its way: {shuttle.leg}')
    check(shuttle.load == {'iron': 30.}, f'carrying: {shuttle.load}')
    check(scenario.base.depot.stock == {'gold': 5.}, 'the rest stays')
    check('En route' in panel().status, f'told: {panel().status}')
    # Not to wait for the whole trip
    shuttle.left = .3


@scenario.step(.6)
def delivers() -> None:
    stock = outpost('ares').post.depot.stock
    check(stock == {'iron': 30.}, f'in the depot of Ares: {stock}')
    shuttle = scenario.base.post.shuttle
    check(shuttle.leg == 'back', f'coming back: {shuttle.leg}')
    check(shuttle.left <= SHUTTLE_MIN_TRIP * 10, 'for as long as it took')
    check('retour' in panel().status, f'told: {panel().status}')
    scenario.press(scenario.button(panel(), 'Fermer'))
    scenario.press(scenario.game.ids.map_button)


@scenario.step(.3)
def shows_on_the_map() -> None:
    shown = scenario.game.ids.map.ids.view.shown
    check(len(shown.shuttles) == 1, f'one on its way: {shown.shuttles}')
    scenario.screenshot('map')
    scenario.game.map_open = False


scenario.run()
