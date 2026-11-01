import math
from random import Random

from app.logic.base.config import (
    DEPOT_CAPACITY,
    SHUTTLE_CLEARANCE,
    SHUTTLE_DOCK_HEIGHT,
    SHUTTLE_LOAD,
    SHUTTLE_SPEED,
    SHUTTLE_SUN_CLEARANCE,
)
from app.logic.base.post import HOME_SERVICES, Post, Services
from app.logic.base.quays import (
    Quay,
    can_send,
    carried_text,
    destination_of,
    shuttle_marks,
    shuttle_position,
    update_shuttles,
)
from app.logic.base.shuttle_flight import Airspace, Obstacle, fly, turned
from app.logic.base.shuttles import Route, Shuttle, ShuttleState, Way
from app.logic.world.space import Celestial, Vec2

IRON = Route('there', ('iron',))
FULL = float(SHUTTLE_LOAD)
OPEN = Airspace((0., 0.), ())
DT = .1
WAY = Way((0., 0.), (1000., 0.))


def shuttle(route: Route | None = IRON) -> Shuttle:
    carrier = Shuttle()
    carrier.route = route
    return carrier


def fly_on(
    carrier: Shuttle,
    here: dict[str, float],
    there: dict[str, float],
    seconds: float
) -> None:
    for _ in range(round(seconds / DT)):
        carrier.update(DT, here, there, WAY, OPEN)


def crossing_time() -> float:
    return 1000. / SHUTTLE_SPEED + 1.


def test_it_waits_without_a_destination() -> None:
    carrier, here = shuttle(), {'iron': FULL}
    carrier.update(1., here, None, WAY, OPEN)
    assert carrier.leg == 'waiting' and here == {'iron': FULL}


def test_it_waits_with_nothing_to_carry() -> None:
    carrier = shuttle()
    carrier.update(1., {}, {}, WAY, OPEN)
    assert carrier.leg == 'waiting'


def test_it_waits_to_leave_full_taking_nothing_yet() -> None:
    carrier, here = shuttle(), {'iron': FULL - 1.}
    carrier.update(1., here, {}, WAY, OPEN)
    assert carrier.leg == 'waiting' and not carrier.load
    assert here == {'iron': FULL - 1.}
    assert carrier.waiting_for(here) == SHUTTLE_LOAD - 1


def test_it_leaves_as_soon_as_it_can_be_full() -> None:
    carrier, here = shuttle(), {'iron': FULL, 'gold': 5.}
    carrier.update(DT, here, {}, WAY, OPEN)
    assert carrier.leg == 'out' and carrier.load == {'iron': FULL}
    assert here == {'gold': 5.}


def test_several_minerals_make_a_full_load_the_first_ones_first() -> None:
    carrier = shuttle(Route('there', ('gold', 'iron')))
    here = {'iron': 500., 'gold': 40.}
    carrier.update(DT, here, {}, WAY, OPEN)
    assert carrier.load == {'gold': 40., 'iron': FULL - 40.}
    assert sum(carrier.load.values()) == SHUTTLE_LOAD


def test_it_only_takes_whole_units() -> None:
    carrier, here = shuttle(), {'iron': FULL + .5}
    carrier.update(DT, here, {}, WAY, OPEN)
    assert carrier.load == {'iron': FULL} and here == {'iron': .5}


def test_a_whole_round_trip() -> None:
    carrier, here = shuttle(), {'iron': FULL}
    there: dict[str, float] = {}
    carrier.update(DT, here, there, WAY, OPEN)
    fly_on(carrier, here, there, crossing_time() - 2.)
    assert not there
    fly_on(carrier, here, there, 2.)
    assert there == {'iron': FULL} and carrier.leg == 'back'
    assert not carrier.load
    fly_on(carrier, here, there, crossing_time())
    assert carrier.state.leg == 'waiting' and carrier.offset is None


def test_what_does_not_fit_comes_back() -> None:
    carrier, here = shuttle(), {'iron': FULL}
    there = {'iron': DEPOT_CAPACITY - 5.}
    carrier.update(DT, here, there, WAY, OPEN)
    fly_on(carrier, here, there, crossing_time())
    assert there['iron'] == DEPOT_CAPACITY
    assert carrier.load == {'iron': FULL - 5.}
    fly_on(carrier, here, there, crossing_time())
    assert here == {'iron': FULL - 5.} and not carrier.load


def test_it_comes_back_as_it_was() -> None:
    carrier, here = shuttle(), {'iron': FULL}
    carrier.update(DT, here, {}, WAY, OPEN)
    fly_on(carrier, here, {}, 2.)
    again = Shuttle()
    again.resume(carrier.state)
    assert again.state == carrier.state
    assert carrier.state != ShuttleState()


def test_it_flies_straight_with_nothing_in_the_way() -> None:
    pos, angle = fly((0., 0.), (100., 0.), [], 10.)
    assert pos == (10., 0.) and angle == 0.


def flight(
    start: Vec2,
    goal: Vec2,
    obstacles: list[Obstacle]
) -> list[Vec2]:
    """ Every step of it, until there """
    pos, trail = start, [start]
    for _ in range(20000):
        pos, _angle = fly(pos, goal, obstacles, 2.5)
        trail.append(pos)
        if math.dist(pos, goal) < 8.:
            return trail
    raise AssertionError(f'never got there: {pos}')


def test_it_rounds_what_stands_in_the_way() -> None:
    planet = Obstacle((500., 0.), 200.)
    trail = flight((0., 0.), (1000., 0.), [planet])
    assert all(math.dist(pos, planet.pos) >= 199.9 for pos in trail)


def test_it_rounds_the_side_closest_to_where_it_goes() -> None:
    planet = Obstacle((500., 0.), 200.)
    trail = flight((0., 50.), (1000., 50.), [planet])
    assert all(pos[1] > -1. for pos in trail)


def test_it_leaves_and_reaches_docks_on_the_far_sides_of_bodies() -> None:
    first = Obstacle((0., 0.), 212.)
    second = Obstacle((1000., 0.), 212.)
    start, goal = (-218., 0.), (1218., 0.)
    trail = flight(start, goal, [first, second])
    assert all(math.dist(pos, first.pos) >= 211.9 for pos in trail)
    assert all(math.dist(pos, second.pos) >= 211.9 for pos in trail)


def test_it_is_pushed_out_of_what_comes_upon_it() -> None:
    planet = Obstacle((0., 0.), 200.)
    pos, _angle = fly((10., 0.), (50., 0.), [planet], 1.)
    assert math.dist(pos, planet.pos) >= 199.9


def test_its_nose_turns_the_short_way_little_by_little() -> None:
    assert 0. < turned(0., 1., .1) < 1.
    assert turned(.1, -.1, .1) < .1
    assert turned(3., -3., .1) > 3.


def quay(key: str, x: float, services: Services = HOME_SERVICES) -> Quay:
    return Quay(
        key, key.upper(), Post(services, Random(1)),
        Celestial(1, 100., pos=(x, 0.)),
    )


def test_a_shuttle_stands_above_its_dock_clear_of_the_body() -> None:
    assert SHUTTLE_DOCK_HEIGHT > SHUTTLE_CLEARANCE
    start = quay('a', 0.)
    assert start.spot == (100. + SHUTTLE_DOCK_HEIGHT, 0.)


def test_only_posts_with_a_depot_are_destinations() -> None:
    start, bare = quay('a', 0.), quay('b', 500., Services(fuel=True))
    start.post.shuttle.route = Route('b', ('iron',))
    assert destination_of(start, [start, bare]) is None
    served = quay('b', 500., Services(depot=True))
    assert destination_of(start, [start, served]) is served


def test_a_dock_needs_a_depot_elsewhere_to_send_to() -> None:
    start = quay('a', 0.)
    bare = quay('b', 500., Services(fuel=True))
    served = quay('c', 900., Services(depot=True))
    assert not can_send(start, [start])
    assert not can_send(start, [start, bare])
    assert can_send(start, [start, bare, served])


def test_no_sending_without_a_dock() -> None:
    start = quay('a', 0., Services(depot=True))
    assert not can_send(start, [start, quay('b', 500.)])


def test_shuttles_only_run_from_docks_built() -> None:
    start = quay('a', 0., Services(depot=True))
    end = quay('b', 500.)
    start.post.shuttle.route = Route('b', ('iron',))
    start.post.depot.stock['iron'] = FULL
    update_shuttles([start, end], OPEN, 1.)
    assert start.post.shuttle.leg == 'waiting'


def test_ore_goes_from_post_to_post_around_their_bodies() -> None:
    start, end = quay('a', 0.), quay('b', 2000.)
    start.post.shuttle.route = Route('b', ('iron',))
    start.post.depot.stock['iron'] = FULL
    airspace = Airspace((0., 0.), [
        Obstacle(q.body.pos, q.body.radius + SHUTTLE_CLEARANCE)
        for q in (start, end)
    ])
    update_shuttles([start, end], airspace, DT)
    assert start.post.shuttle.leg == 'out'
    for _ in range(400):
        update_shuttles([start, end], airspace, DT)
    assert end.post.depot.stock == {'iron': FULL}


def test_it_keeps_flying_when_the_sun_moves_with_the_world() -> None:
    carrier, here = shuttle(), {'iron': FULL}
    carrier.update(DT, here, {}, WAY, OPEN)
    fly_on(carrier, here, {}, 1.)
    before = carrier.offset
    moved = Airspace((5000., 0.), ())
    carrier.update(
        0., here, {}, Way((5000., 0.), (6000., 0.)), moved,
    )
    assert carrier.offset == before


def test_the_sun_keeps_shuttles_further_off() -> None:
    assert SHUTTLE_SUN_CLEARANCE > SHUTTLE_CLEARANCE


def test_the_map_tells_where_it_goes_and_what_it_carries() -> None:
    start, end = quay('a', 0.), quay('b', 2000.)
    start.post.shuttle.route = Route('b', ('iron', 'gold'))
    assert shuttle_position(start, (0., 0.)) is None
    assert shuttle_marks([start, end], (0., 0.)) == []
    start.post.depot.stock.update({'iron': 60., 'gold': 40.})
    update_shuttles([start, end], OPEN, DT)
    update_shuttles([start, end], OPEN, DT)
    mark, = shuttle_marks([start, end], (0., 0.))
    assert mark.way == 'A vers B'
    assert mark.carried == '60 Fer · 40 Or'


def test_an_empty_shuttle_says_so() -> None:
    assert carried_text({}) == 'À vide'
