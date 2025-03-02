import math

import pytest

from app.logic.ship.config import (
    LANDING_MAX_SPEED,
    SHIP_DRAG,
)
from app.logic.ship.ship import Ship, is_crash
from app.logic.ship.shipyard import ShipStats
from app.logic.world.config import (
    GRAVITY,
    SUN_GRAVITY,
    SUN_GRAVITY_FALLOFF,
    SUN_RADIUS,
)
from app.logic.world.space import Celestial, Orbit, Vec2

from .fakes import FakeBody

DT = 1 / 60
SHIP_LENGTH = 40.
SHIP_MAX_SPEED = 500.
STATS = ShipStats(
    max_speed=SHIP_MAX_SPEED, thrust=1.5, turn_speed=8., capacity=60.,
    laser=1, scan=0., size=(SHIP_LENGTH, 25.),
)


def make_ship(position: Vec2 = (0., 0.), velocity: Vec2 = (0., 0.),
              angle: float = 0.) -> tuple[Ship, FakeBody]:
    body = FakeBody(position, velocity, angle)
    return Ship(0, body, STATS), body


def make_sun() -> Celestial:
    return Celestial(
        0, SUN_RADIUS, gravity=SUN_GRAVITY,
        gravity_falloff=SUN_GRAVITY_FALLOFF, gravity_range=None,
    )


def fly(ship: Ship, body: FakeBody, seconds: float,
        heading: float | None, attractors: list[Celestial]) -> None:
    for _ in range(round(seconds / DT)):
        ship.update(DT, heading, attractors)
        body.step(DT)


def speed(body: FakeBody) -> float:
    return math.hypot(*body.velocity)


def test_thrust_reaches_max_speed_towards_the_heading() -> None:
    ship, body = make_ship()
    fly(ship, body, 5., math.pi / 4, [])
    vx, vy = body.velocity
    assert speed(body) == pytest.approx(SHIP_MAX_SPEED, rel=.01)
    assert math.atan2(vy, vx) == pytest.approx(math.pi / 4)
    assert body.angle == pytest.approx(math.pi / 4)


def test_ship_turns_the_short_way() -> None:
    ship, body = make_ship(angle=.1)
    ship.drive(DT, -.1 + 2 * math.pi, (0., 0.))
    assert -.1 < body.angle < .1


def test_collisions_do_not_make_the_ship_spin() -> None:
    ship, body = make_ship()
    body.angular_velocity = 3.
    ship.drive(DT, None, (0., 0.))
    assert body.angular_velocity == 0


def test_coasting_slows_down_progressively() -> None:
    ship, body = make_ship(velocity=(300., 0.))
    fly(ship, body, 1., None, [])
    assert speed(body) == pytest.approx(300. * math.exp(-SHIP_DRAG), rel=.01)


def test_coasting_ship_moves_with_its_reference() -> None:
    ship, body = make_ship()
    for _ in range(round(20 / DT)):
        ship.drive(DT, None, (30., -10.))
    assert body.velocity == pytest.approx((30., -10.), rel=.01)


def test_reference_is_the_strongest_attractor() -> None:
    sun = make_sun()
    planet = Celestial(
        1, 200., orbit=Orbit(sun, 5000., 25., 0.), gravity=GRAVITY * 200.,
    )
    near_planet, _ = make_ship(position=(5000., -250.))
    far_from_planets, _ = make_ship(position=(-5000., 0.))
    assert near_planet.reference_velocity([sun, planet]) == planet.velocity
    assert far_from_planets.reference_velocity([sun, planet]) == (0., 0.)


def test_gravity_accelerates_towards_the_attractor() -> None:
    ship, body = make_ship(position=(2 * SUN_RADIUS, 0.))
    ship.apply_gravity(1., [make_sun()])
    assert body.velocity == pytest.approx((-SUN_GRAVITY / 2, 0.))


def test_idle_ship_falls_towards_the_sun() -> None:
    ship, body = make_ship(position=(5400., 0.))
    fly(ship, body, 10., None, [make_sun()])
    assert body.position.x < 5400. - 500.
    assert body.velocity.x < 0


def test_ship_can_escape_the_sun_from_its_surface() -> None:
    start = SUN_RADIUS + SHIP_LENGTH
    ship, body = make_ship(position=(start, 0.))
    fly(ship, body, 3., 0., [make_sun()])
    assert body.position.x > start + 500.


# Crashes

def test_touching_anything_but_the_earth_is_a_crash() -> None:
    assert is_crash(0., on_earth=False)


def test_landing_on_the_earth() -> None:
    assert not is_crash(LANDING_MAX_SPEED / 2, on_earth=True)
    assert is_crash(LANDING_MAX_SPEED * 2, on_earth=True)


# Mining

def test_nose_is_in_front_of_the_ship() -> None:
    ship, _ = make_ship(position=(100., 100.), angle=math.pi / 2)
    assert ship.nose == pytest.approx((100., 100. + SHIP_LENGTH / 2))
