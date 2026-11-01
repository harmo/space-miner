from random import Random

import pytest

from app.logic.base.config import (
    DEPOT_CAPACITY,
    SHUTTLE_LOAD,
    SHUTTLE_MIN_TRIP,
    SHUTTLE_SPEED,
)
from app.logic.base.post import HOME_SERVICES, Post, Services
from app.logic.base.quays import (
    Quay,
    destination_of,
    shuttle_position,
    trip_time,
    update_shuttles,
)
from app.logic.base.shuttles import Route, Shuttle, ShuttleState
from app.logic.world.space import Celestial

TRIP = 30.
IRON = Route('there', ('iron',))


def shuttle(route: Route | None = IRON) -> Shuttle:
    carrier = Shuttle()
    carrier.route = route
    return carrier


def test_it_waits_without_a_destination() -> None:
    carrier, here = shuttle(), {'iron': 10.}
    carrier.update(1., here, None, 0.)
    assert carrier.leg == 'waiting' and here == {'iron': 10.}


def test_it_waits_with_nothing_to_carry() -> None:
    carrier = shuttle()
    carrier.update(1., {}, {}, TRIP)
    assert carrier.leg == 'waiting'


def test_it_loads_what_was_chosen_and_leaves() -> None:
    carrier, here = shuttle(), {'iron': 10., 'gold': 5.}
    carrier.update(.1, here, {}, TRIP)
    assert carrier.leg == 'out' and carrier.load == {'iron': 10.}
    assert here == {'gold': 5.}


def test_it_carries_a_full_load_at_most_the_first_minerals_first() -> None:
    carrier = shuttle(Route('there', ('gold', 'iron')))
    here = {'iron': 500., 'gold': 40.}
    carrier.update(.1, here, {}, TRIP)
    assert carrier.load == {'gold': 40., 'iron': SHUTTLE_LOAD - 40.}
    assert sum(carrier.load.values()) == SHUTTLE_LOAD


def test_it_only_takes_whole_units() -> None:
    carrier, here = shuttle(), {'iron': 7.5}
    carrier.update(.1, here, {}, TRIP)
    assert carrier.load == {'iron': 7.} and here == {'iron': .5}


def test_a_whole_round_trip() -> None:
    carrier, here = shuttle(), {'iron': 10.}
    there: dict[str, float] = {}
    carrier.update(.1, here, there, TRIP)
    carrier.update(TRIP - 1., here, there, TRIP)
    assert not there
    carrier.update(2., here, there, TRIP)
    assert there == {'iron': 10.} and carrier.leg == 'back'
    assert not carrier.load
    carrier.update(TRIP + 1., here, there, TRIP)
    assert carrier.state.leg == 'waiting'


def test_what_does_not_fit_comes_back() -> None:
    carrier = shuttle()
    here = {'iron': 20.}
    there = {'iron': DEPOT_CAPACITY - 5.}
    carrier.update(.1, here, there, TRIP)
    carrier.update(TRIP + 1., here, there, TRIP)
    assert there['iron'] == DEPOT_CAPACITY
    assert carrier.load == {'iron': 15.}
    carrier.update(TRIP + 1., here, there, TRIP)
    assert here == {'iron': 15.} and not carrier.load


def test_it_comes_back_as_it_was() -> None:
    carrier = shuttle()
    carrier.update(.1, {'iron': 10.}, {}, TRIP)
    carrier.update(5., {}, {}, TRIP)
    again = Shuttle()
    again.resume(carrier.state)
    assert again.state == carrier.state
    assert carrier.state != ShuttleState()


def quay(key: str, x: float, services: Services = HOME_SERVICES) -> Quay:
    return Quay(
        key, key, Post(services, Random(1)),
        Celestial(1, 100., pos=(x, 0.)),
    )


def test_trips_take_as_long_as_the_way_is_long() -> None:
    far = 10 * SHUTTLE_SPEED * SHUTTLE_MIN_TRIP
    assert trip_time(quay('a', 0.), quay('b', far)) == (
        pytest.approx(10 * SHUTTLE_MIN_TRIP)
    )
    assert trip_time(quay('a', 0.), quay('b', 10.)) == SHUTTLE_MIN_TRIP


def test_only_posts_with_a_depot_are_destinations() -> None:
    start, bare = quay('a', 0.), quay('b', 500., Services(fuel=True))
    start.post.shuttle.route = Route('b', ('iron',))
    assert destination_of(start, [start, bare]) is None
    served = quay('b', 500., Services(depot=True))
    assert destination_of(start, [start, served]) is served


def test_shuttles_only_run_from_docks_built() -> None:
    start = quay('a', 0., Services(depot=True))
    end = quay('b', 500.)
    start.post.shuttle.route = Route('b', ('iron',))
    start.post.depot.stock['iron'] = 10.
    update_shuttles([start, end], 1.)
    assert start.post.shuttle.leg == 'waiting'


def test_ore_goes_from_post_to_post() -> None:
    start, end = quay('a', 0.), quay('b', 500.)
    start.post.shuttle.route = Route('b', ('iron',))
    start.post.depot.stock['iron'] = 10.
    update_shuttles([start, end], .1)
    assert start.post.shuttle.leg == 'out'
    update_shuttles([start, end], SHUTTLE_MIN_TRIP + 1.)
    assert end.post.depot.stock == {'iron': 10.}


def test_a_shuttle_on_its_way_lies_between_posts() -> None:
    start, end = quay('a', 0.), quay('b', 1000.)
    assert shuttle_position(start, [start, end]) is None
    start.post.shuttle.route = Route('b', ('iron',))
    start.post.depot.stock['iron'] = 10.
    update_shuttles([start, end], .1)
    update_shuttles([start, end], SHUTTLE_MIN_TRIP / 2)
    pos = shuttle_position(start, [start, end])
    assert pos is not None and 400. < pos[0] < 600.
