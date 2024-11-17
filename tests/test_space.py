import math

import pytest

from app.logic.config import STAR_TILE, WORLD_SIZE
from app.logic.world.config import SUN_GRAVITY, SUN_GRAVITY_FALLOFF, SUN_RADIUS
from app.logic.world.space import (
    Celestial,
    Orbit,
    Vec2,
    angle_diff,
    closest_to,
    nearest,
    strongest,
    wrap_shift,
)


def attractor(gravity: float = 100., falloff: float = 2.,
              gravity_range: float | None = None) -> Celestial:
    """ Radius 10 at the origin """
    return Celestial(
        0, 10., gravity=gravity, gravity_falloff=falloff,
        gravity_range=gravity_range,
    )


# Periodic space

def test_wrap_shift_keeps_close_positions() -> None:
    assert wrap_shift((100., -200.), (0., 0.)) == (0, 0)


def test_wrap_shift_brings_far_positions_back() -> None:
    assert wrap_shift((WORLD_SIZE * .6, 0.), (0., 0.)) == (-WORLD_SIZE, 0)
    assert wrap_shift((0., -WORLD_SIZE * 1.7), (0., 0.)) == (
        0, 2 * WORLD_SIZE
    )


@pytest.mark.parametrize('pos', [
    (17000., 3.), (-19000., 40000.), (95000., -95000.),
])
def test_wrapped_position_is_within_half_a_period(pos: Vec2) -> None:
    center = (1000., -2000.)
    shift_x, shift_y = wrap_shift(pos, center)
    assert abs(pos[0] + shift_x - center[0]) <= WORLD_SIZE / 2
    assert abs(pos[1] + shift_y - center[1]) <= WORLD_SIZE / 2


def test_wrap_shift_with_another_period() -> None:
    assert wrap_shift((STAR_TILE * .8, 0.), (0., 0.), STAR_TILE) == (
        -STAR_TILE, 0
    )


def test_star_field_survives_world_recentering() -> None:
    # Moving everything by WORLD_SIZE must leave the star field unchanged
    assert WORLD_SIZE % STAR_TILE == 0


@pytest.mark.parametrize('a, b, expected', [
    (.5, .2, .3), (.2, .5, -.3),
    (math.pi - .1, -math.pi + .1, -.2), (-math.pi + .1, math.pi - .1, .2),
    (7 * math.pi, 0., math.pi),
])
def test_angle_diff_is_the_shortest_turn(a: float, b: float,
                                         expected: float) -> None:
    assert abs(angle_diff(a, b) - expected) < 1e-9 or (
        abs(expected) == pytest.approx(math.pi)
        and abs(angle_diff(a, b)) == pytest.approx(math.pi)
    )


# Orbits

def test_orbit_position_around_parent() -> None:
    parent = Celestial(0, 10., pos=(100., 50.))
    orbit = Orbit(parent, 200., speed=40., angle=0.)
    assert orbit.position == pytest.approx((300., 50.))


def test_orbit_advances_at_its_speed() -> None:
    orbit = Orbit(Celestial(0, 10.), 200., speed=40., angle=0.)
    orbit.advance(1.)
    assert orbit.angle * orbit.radius == pytest.approx(40.)


def test_orbit_velocity_is_tangent() -> None:
    orbit = Orbit(Celestial(0, 10.), 200., speed=40., angle=0.)
    assert orbit.velocity == pytest.approx((0., 40.))


def test_negative_speed_turns_clockwise() -> None:
    orbit = Orbit(Celestial(0, 10.), 200., speed=-40., angle=0.)
    assert orbit.velocity == pytest.approx((0., -40.))


def test_satellite_velocity_includes_its_parent_velocity() -> None:
    sun = Celestial(0, 600.)
    planet = Celestial(1, 100., orbit=Orbit(sun, 1000., 30., 0.))
    moon = Celestial(2, 10., orbit=Orbit(planet, 150., 10., math.pi / 2))
    assert planet.velocity == pytest.approx((0., 30.))
    assert moon.velocity == pytest.approx((-10., 30.))


def test_moving_the_sun_moves_its_satellites() -> None:
    sun = Celestial(0, 600.)
    planet = Celestial(1, 100., orbit=Orbit(sun, 1000., 30., 0.))
    moon = Celestial(2, 10., orbit=Orbit(planet, 150., 10., 0.))
    sun.shift((500., -20.))
    assert planet.pos == pytest.approx((1500., -20.))
    assert moon.pos == pytest.approx((1650., -20.))


# Stations


# Gravity

def test_pull_at_the_surface_is_the_gravity() -> None:
    assert attractor().pull(10., 0.) == pytest.approx((-100., 0.))


def test_pull_points_to_the_center() -> None:
    pull_x, pull_y = attractor().pull(30., 40.)
    assert pull_x < 0 and pull_y < 0
    assert pull_y / pull_x == pytest.approx(40. / 30.)


@pytest.mark.parametrize('falloff, expected', [(2., 25.), (1., 50.)])
def test_pull_fades_with_distance(falloff: float, expected: float) -> None:
    pull_x, _ = attractor(falloff=falloff).pull(20., 0.)
    assert -pull_x == pytest.approx(expected)


def test_pull_is_capped_inside_the_body() -> None:
    assert attractor().pull(5., 0.) == pytest.approx((-100., 0.))


def test_no_pull_out_of_range() -> None:
    planet = attractor(gravity_range=6.)
    assert planet.pull(59., 0.) != (0., 0.)
    assert planet.pull(61., 0.) == (0., 0.)


def test_no_gravity_no_pull() -> None:
    assert Celestial(0, 10.).pull(10., 0.) == (0., 0.)


def test_sun_pulls_from_anywhere_in_the_world() -> None:
    sun = Celestial(
        0, SUN_RADIUS, gravity=SUN_GRAVITY,
        gravity_falloff=SUN_GRAVITY_FALLOFF, gravity_range=None,
    )
    far = WORLD_SIZE / 2
    pull_x, _ = sun.pull(far, 0.)
    assert -pull_x == pytest.approx(SUN_GRAVITY * SUN_RADIUS / far)


# Neighbors

def test_nearest_body_within_a_distance() -> None:
    bodies = [Celestial(i, 5., pos=(x, 0.)) for i, x in enumerate((50., 300.))]
    assert nearest((0., 0.), bodies, 100.) is bodies[0]
    assert nearest((280., 0.), bodies, 100.) is bodies[1]
    assert nearest((1000., 0.), bodies, 100.) is None


def test_strongest_attractor() -> None:
    sun = Celestial(0, 600., gravity=400., gravity_falloff=1.,
                    gravity_range=None)
    planet = Celestial(1, 200., pos=(5000., 0.), gravity=250.)
    assert strongest((5250., 0.), [sun, planet]) is planet
    assert strongest((-3000., 0.), [sun, planet]) is sun
    assert strongest((0., 0.), []) is None


def test_closest_thing_under_a_click() -> None:
    small = Celestial(0, 5., pos=(100., 0.))
    big = Celestial(1, 50., pos=(160., 0.))
    # Measured to the edge: the big one is closer to (115, 0)
    assert closest_to((115., 0.), [small, big], 40.) is big
    assert closest_to((90., 0.), [small, big], 40.) is small
    assert closest_to((0., 500.), [small, big], 40.) is None
