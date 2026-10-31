from random import Random

import pytest

from app.logic.ship.config import LANDING_RANGE
from app.logic.world.config import (
    CERES_BELT_ASTEROIDS,
    CERES_BELT_ORBITS,
    CERES_RADIUS,
    REGROW_THRESHOLD,
    REGROW_TIME,
    SWARM_ASTEROIDS,
    SWARM_EVERY,
    SWARM_STAYS,
)
from app.logic.world.layout import plan_ceres_belt, plan_system, sun_belt_orbit
from app.logic.world.regrowth import Regrowth
from app.logic.world.swarms import RICH, SwarmClock, plan_swarm

FULL = 30


def test_no_regrowth_above_the_threshold() -> None:
    regrowth = Regrowth(FULL)
    above = int(FULL * REGROW_THRESHOLD) + 1
    assert regrowth.update(above, REGROW_TIME) == 0


def test_below_it_asteroids_come_back_one_at_a_time() -> None:
    regrowth = Regrowth(FULL)
    count = int(FULL * REGROW_THRESHOLD) - 1
    assert regrowth.update(count, regrowth.period * .5) == 0
    assert regrowth.update(count, regrowth.period * .6) == 1


def test_it_goes_on_until_full_past_the_threshold() -> None:
    regrowth = Regrowth(FULL)
    count = 0
    seconds = 0.
    while count < FULL:
        count += regrowth.update(count, 1.)
        seconds += 1.
    assert seconds == pytest.approx(REGROW_TIME, abs=2)
    assert regrowth.update(count, REGROW_TIME) == 0
    assert not regrowth.growing


def test_never_more_than_full() -> None:
    regrowth = Regrowth(FULL)
    assert regrowth.update(FULL - 1, 0.) == 0      # above the threshold
    regrowth.growing = True
    assert regrowth.update(FULL - 1, REGROW_TIME * 10) == 1


def test_belts_are_planned_to_grow_back() -> None:
    plan = plan_system(Random(1))
    sun_belt = plan.belts[-1]
    assert sun_belt.parent is None
    low, high = sun_belt.orbits
    assert low < sun_belt_orbit(plan.orbits) < high
    assert len(plan.sun_belt) == sun_belt.full
    for belt in plan.belts[:-1]:
        assert belt.parent is not None
        planet = plan.planets[belt.parent]
        assert len(planet.satellites) == belt.full
    asteroid = sun_belt.asteroid(Random(2), angle=1.)
    assert asteroid.orbit_angle == 1. and low <= asteroid.orbit_radius <= high


def test_swarms_are_rich_and_gathered() -> None:
    orbits = plan_system(Random(3)).orbits
    swarm = plan_swarm(Random(3), orbits)
    assert any(inner < swarm.distance < outer
               for inner, outer in zip(orbits, orbits[1:], strict=False))
    assert len(swarm.asteroids) == SWARM_ASTEROIDS
    assert all(asteroid.mineral in RICH for asteroid in swarm.asteroids)
    angles = [asteroid.orbit_angle for asteroid in swarm.asteroids]
    assert max(angles) - min(angles) < .2
    for asteroid in swarm.asteroids:
        assert abs(asteroid.orbit_radius - swarm.distance) < 200


def test_swarms_come_and_leave() -> None:
    clock = SwarmClock(Random(4))
    changes = []
    for _ in range(int((SWARM_EVERY[1] + SWARM_STAYS) * 2)):
        change = clock.update(1.)
        if change:
            changes.append(change)
    assert changes[:3] == ['arrives', 'leaves', 'arrives']


def test_a_belt_kept_full_grows_back_from_one_missing() -> None:
    regrowth = Regrowth(FULL, 60., 1.)
    assert regrowth.update(FULL - 1, regrowth.period) == 1
    assert regrowth.update(FULL, 1.) == 0


def test_the_belt_of_ceres_is_the_fullest_and_quickest() -> None:
    belt = plan_ceres_belt()
    plan = plan_system(Random(1))
    assert belt.full == CERES_BELT_ASTEROIDS
    assert all(belt.full > other.full for other in plan.belts[:-1])
    assert all(belt.regrow_time < other.regrow_time for other in plan.belts)
    near_the_sun = plan.belts[-1]
    area = near_the_sun.orbits[1] ** 2 - near_the_sun.orbits[0] ** 2
    own_area = belt.orbits[1] ** 2 - belt.orbits[0] ** 2
    assert belt.full / own_area > 4 * near_the_sun.full / area


def test_the_belt_of_ceres_leaves_room_to_land() -> None:
    inner, _ = CERES_BELT_ORBITS
    assert inner - CERES_RADIUS > LANDING_RANGE


def test_asteroids_of_ceres_turn_at_their_own_speed() -> None:
    belt = plan_ceres_belt()
    asteroid = belt.asteroid(Random(2))
    assert belt.speeds[0] <= asteroid.speed <= belt.speeds[1]
