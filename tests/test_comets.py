import math
from random import Random

import pytest

from app.logic.world.comets import (
    CometClock,
    CometOrbit,
    debris_shed,
    plan_comet,
    plan_debris,
    tail_length,
)
from app.logic.world.config import (
    COMET_DEBRIS,
    COMET_DEBRIS_ORBIT,
    COMET_EVERY,
    COMET_ICE,
    COMET_PERIHELION,
    COMET_TAIL,
    COMET_TAIL_RANGE,
    COMET_TIME,
)
from app.logic.world.space import Celestial
from app.logic.world.swarms import RICH

CLOSEST, FARTHEST = 1100., 25000.


def sun() -> Celestial:
    return Celestial(0, 600., pos=(1000., 500.))


def comet(tilt: float = 0., sense: int = 1) -> CometOrbit:
    return CometOrbit(sun(), CLOSEST, FARTHEST, 480., tilt, sense)


def distance(orbit: CometOrbit) -> float:
    return math.dist(orbit.position, orbit.parent.pos)


def test_a_comet_starts_at_the_far_end() -> None:
    assert distance(comet()) == pytest.approx(FARTHEST)


def test_a_comet_races_by_the_sun_halfway() -> None:
    orbit = comet()
    orbit.advance(240.)
    assert distance(orbit) == pytest.approx(CLOSEST)
    assert orbit.until_closest == pytest.approx(0.)


def test_a_comet_is_slow_far_away_and_fast_close_by() -> None:
    orbit = comet()
    far = math.hypot(*orbit.velocity)
    orbit.advance(240.)
    close = math.hypot(*orbit.velocity)
    assert close > 15 * far


def test_kepler_equal_areas_in_equal_times() -> None:
    orbit = comet()
    x, y = orbit.parent.pos
    areas = []
    for _ in range(40):
        area = 0.
        for _ in range(48):
            ax, ay = orbit.position
            orbit.advance(.25)
            bx, by = orbit.position
            area += abs((ax - x) * (by - y) - (ay - y) * (bx - x)) / 2
        areas.append(area)
    assert max(areas) == pytest.approx(min(areas), rel=.05)


@pytest.mark.parametrize('sense', [1, -1])
def test_velocity_matches_the_way_a_comet_moves(sense: int) -> None:
    orbit = comet(1., sense)
    orbit.advance(200.)
    ax, ay = orbit.position
    velocity = orbit.velocity
    orbit.advance(.001)
    bx, by = orbit.position
    assert ((bx - ax) / .001, (by - ay) / .001) == pytest.approx(
        velocity, rel=1e-2,
    )


def test_a_comet_leaves_once_back_at_the_far_end() -> None:
    orbit = comet()
    orbit.advance(479.)
    assert not orbit.over and orbit.left == pytest.approx(1.)
    orbit.advance(2.)
    assert orbit.over


def test_the_path_of_a_comet_closes_on_itself() -> None:
    path = comet().path(60)
    assert path[0] == pytest.approx(path[-1])
    assert min(math.dist(pos, (1000., 500.)) for pos in path) == (
        pytest.approx(CLOSEST)
    )


def test_a_planned_comet_comes_from_the_last_planet() -> None:
    orbit = plan_comet(Random(1), sun(), (2000., 25000.))
    assert distance(orbit) == pytest.approx(25000.)
    orbit.advance(COMET_TIME / 2)
    assert distance(orbit) == pytest.approx(600. + COMET_PERIHELION)


def test_the_tail_grows_towards_the_sun() -> None:
    assert tail_length(COMET_TAIL_RANGE + 1.) == 0.
    assert 0 < tail_length(6000.) < tail_length(1000.) < COMET_TAIL
    assert tail_length(0.) == COMET_TAIL


def test_comets_come_now_and_then() -> None:
    clock = CometClock(Random(2))
    assert not clock.due(COMET_EVERY[0] - 1)
    assert clock.due(COMET_EVERY[1])
    assert COMET_EVERY[0] <= clock.waiting <= COMET_EVERY[1]


def test_a_comet_sheds_more_and_more_on_its_way_to_the_sun() -> None:
    assert debris_shed(COMET_TAIL_RANGE * 2) == COMET_ICE
    assert COMET_ICE < debris_shed(6000.) < debris_shed(1000.)
    assert debris_shed(0.) == COMET_ICE + COMET_DEBRIS


def test_a_comet_sheds_ice_first_then_richer_and_richer() -> None:
    rng = Random(3)
    assert plan_debris(rng, 0).mineral == 'ice'
    last = [plan_debris(rng, COMET_ICE + COMET_DEBRIS - 1) for _ in range(40)]
    assert all(plan.mineral in RICH for plan in last)


def test_what_it_sheds_turns_around_it() -> None:
    low, high = COMET_DEBRIS_ORBIT
    assert low <= plan_debris(Random(4), 0).orbit_radius <= high
