import math
from itertools import pairwise
from random import Random

import pytest

from app.logic.config import MOON, PLANETS, SUN_DISC, WORLD_SIZE
from app.logic.mining.minerals import (
    ASTEROID_SHAPES,
    MINERALS,
    asteroid_texture,
)
from app.logic.world.config import (
    BELT_ASTEROIDS,
    BELT_COUNT,
    BELT_WIDTH,
    EARTH_ORBIT,
    EARTH_RADIUS,
    GRAVITY,
    MOON_ORBIT,
    SUN_BELT_ASTEROIDS,
    SUN_BELT_WIDTH,
    SUN_RADIUS,
)
from app.logic.world.layout import (
    OrbiterPlan,
    SystemPlan,
    orbital_speed,
    plan_system,
    sun_belt_orbit,
)

# Moving the solar system to its copy must happen out of sight: farther
# than half the diagonal of a large screen
OUT_OF_SIGHT = 2000.


@pytest.fixture(params=range(20))
def plan(request: pytest.FixtureRequest) -> SystemPlan:
    seed: int = request.param
    return plan_system(Random(seed))


def test_same_seed_same_plan() -> None:
    assert plan_system(Random(1)) == plan_system(Random(1))


def test_every_planet_texture_once(plan: SystemPlan) -> None:
    textures = [p.planet.texture for p in plan.planets]
    assert sorted(textures) == sorted([*PLANETS, 'earth'])


def test_planets_are_farther_apart_outwards(plan: SystemPlan) -> None:
    orbits = [p.planet.orbit_radius for p in plan.planets]
    speeds = [p.planet.speed for p in plan.planets]
    assert orbits == sorted(orbits)
    gaps = [outer - inner for inner, outer in pairwise(plan.orbits)]
    assert gaps[-1] > 2 * gaps[0]
    assert all(s > 0 for s in speeds)
    assert speeds == sorted(speeds, reverse=True)


def test_gaps_differ_from_game_to_game() -> None:
    assert plan_system(Random(1)).orbits != plan_system(Random(2)).orbits


def test_planets_are_upright_and_pull(plan: SystemPlan) -> None:
    for planet_plan in plan.planets:
        planet = planet_plan.planet
        assert (planet.rotation, planet.spin) == (0., 0.)
        assert planet.gravity == GRAVITY * planet.radius


def test_earth_has_the_moon(plan: SystemPlan) -> None:
    assert plan.earth == EARTH_ORBIT
    earth = plan.planets[plan.earth]
    assert (earth.planet.texture, earth.planet.radius) == (
        'earth', EARTH_RADIUS
    )
    assert [(s.texture, s.orbit_radius) for s in earth.satellites] == [
        (MOON, MOON_ORBIT)
    ]


def test_asteroid_belts(plan: SystemPlan) -> None:
    belts = [
        p for i, p in enumerate(plan.planets)
        if i != plan.earth and p.satellites
    ]
    assert len(belts) == BELT_COUNT
    for belt in belts:
        assert len(belt.satellites) == BELT_ASTEROIDS
        assert len({s.speed > 0 for s in belt.satellites}) == 1
        for asteroid in belt.satellites:
            check_asteroid(asteroid)
            gap = asteroid.orbit_radius - belt.planet.radius
            assert BELT_WIDTH[0] <= gap <= BELT_WIDTH[1]


def check_asteroid(asteroid: OrbiterPlan) -> None:
    assert asteroid.mineral in MINERALS
    assert asteroid.texture in [
        asteroid_texture(asteroid.mineral, shape) for shape in ASTEROID_SHAPES
    ]


def test_belts_mix_minerals(plan: SystemPlan) -> None:
    asteroids = [*plan.sun_belt] + [
        asteroid for p in plan.planets[plan.earth + 1:]
        for asteroid in p.satellites
    ]
    assert len({asteroid.mineral for asteroid in asteroids}) >= 4


def test_sparse_belt_around_the_sun(plan: SystemPlan) -> None:
    assert len(plan.sun_belt) == SUN_BELT_ASTEROIDS
    middle = sun_belt_orbit(plan.orbits)
    for asteroid in plan.sun_belt:
        check_asteroid(asteroid)
        assert abs(asteroid.orbit_radius - middle) <= SUN_BELT_WIDTH / 2
        # Same way as the planets, at about their speed
        assert asteroid.speed == pytest.approx(
            orbital_speed(asteroid.orbit_radius), rel=.15
        )


def test_sun_belt_is_between_the_fourth_and_fifth(plan: SystemPlan) -> None:
    fourth, fifth = plan.planets[3], plan.planets[4]
    belt_inner = min(a.orbit_radius - a.radius for a in plan.sun_belt)
    belt_outer = max(a.orbit_radius + a.radius for a in plan.sun_belt)
    assert belt_inner > fourth.planet.orbit_radius + fourth.extent
    assert belt_outer < fifth.planet.orbit_radius - fifth.extent


def test_planets_never_overlap(plan: SystemPlan) -> None:
    planets = plan.planets
    sun_extent = SUN_RADIUS / SUN_DISC   # with its glow
    assert planets[0].planet.orbit_radius - planets[0].extent > sun_extent
    for inner, outer in pairwise(planets):
        gap = outer.planet.orbit_radius - inner.planet.orbit_radius
        assert gap > inner.extent + outer.extent


def test_system_fits_in_the_repeated_world(plan: SystemPlan) -> None:
    last = plan.planets[-1]
    system_radius = last.planet.orbit_radius + last.extent
    assert WORLD_SIZE / 2 - system_radius > OUT_OF_SIGHT


def test_the_moon_shows_the_earth_always_the_same_face(
        plan: SystemPlan) -> None:
    [moon] = plan.planets[plan.earth].satellites
    assert moon.locked
    # Facing the Earth at first
    assert moon.rotation == pytest.approx(moon.orbit_angle + math.pi)
    # Then turning as fast as it goes round
    assert math.radians(moon.spin) == pytest.approx(
        moon.speed / moon.orbit_radius
    )
