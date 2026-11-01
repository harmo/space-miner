import math

import pytest

from app.logic.ship.config import (
    LANDING_MAX_SPEED,
    LASER_RANGE,
    MINING_DISTANCE,
    SHIP_DRAG,
)
from app.logic.ship.pose import Pose, ShipSize
from app.logic.ship.ship import Ship, is_crash
from app.logic.ship.shipyard import ShipStats
from app.logic.world.config import (
    GRAVITY,
    SUN_GRAVITY,
    SUN_GRAVITY_FALLOFF,
    SUN_RADIUS,
)
from app.logic.world.space import Celestial, Orbit, Station, Vec2, angle_diff

from .fakes import FakeBody

DT = 1 / 60
SHIP_LENGTH = 40.
SHIP_MAX_SPEED = 500.
STATS = ShipStats(
    max_speed=SHIP_MAX_SPEED, thrust=1.5, turn_speed=8., capacity=60.,
    laser=1, scan=0., size=ShipSize(SHIP_LENGTH, 25.),
)


def make_ship(
    position: Vec2 = (0., 0.),
    velocity: Vec2 = (0., 0.),
    angle: float = 0.
) -> tuple[Ship, FakeBody]:
    body = FakeBody(position, velocity, angle)
    return Ship(0, body, STATS), body


def make_sun() -> Celestial:
    return Celestial(
        0, SUN_RADIUS, gravity=SUN_GRAVITY,
        gravity_falloff=SUN_GRAVITY_FALLOFF, gravity_range=None,
    )


def fly(
    ship: Ship,
    body: FakeBody,
    seconds: float,
    heading: float | None,
    attractors: list[Celestial]
) -> None:
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


def test_coasting_ship_glides_on() -> None:
    ship, body = make_ship(velocity=(300., 0.))
    fly(ship, body, 5., None, [])
    assert speed(body) > 300. * .75


def test_coasting_ship_moves_with_its_reference() -> None:
    ship, body = make_ship()
    for _ in range(round(120 / DT)):
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
    # Twice as far from the center as its surface, in 1/distance²
    assert body.velocity == pytest.approx((-SUN_GRAVITY / 4, 0.))


def test_idle_ship_falls_towards_the_sun() -> None:
    ship, body = make_ship(position=(5400., 0.))
    fly(ship, body, 10., None, [make_sun()])
    # Slowly, far from it
    assert 5400. - 500. < body.position.x < 5400. - 100.
    assert body.velocity.x < 0


def test_ship_can_escape_the_sun_from_its_surface() -> None:
    start = SUN_RADIUS + SHIP_LENGTH
    ship, body = make_ship(position=(start, 0.))
    fly(ship, body, 3., 0., [make_sun()])
    assert body.position.x > start + 500.


# Crashes

def test_touching_anything_but_the_earth_is_a_crash() -> None:
    assert is_crash(0., landable=False)


def test_landing_on_the_earth() -> None:
    assert not is_crash(LANDING_MAX_SPEED / 2, landable=True)
    assert is_crash(LANDING_MAX_SPEED * 2, landable=True)


# Mining

def test_nose_is_in_front_of_the_ship() -> None:
    ship, _ = make_ship(position=(100., 100.), angle=math.pi / 2)
    assert ship.nose == pytest.approx((100., 100. + SHIP_LENGTH / 2))


def make_belt() -> tuple[Celestial, Celestial, Celestial]:
    """ A sun, a planet and one of its asteroids """
    sun = make_sun()
    planet = Celestial(
        1, 250., orbit=Orbit(sun, 7000., 22., 0.), gravity=GRAVITY * 250.,
    )
    asteroid = Celestial(2, 8., orbit=Orbit(planet, 450., 50., 0.))
    return sun, planet, asteroid


def hold(
    ship: Ship,
    body: FakeBody,
    seconds: float,
    system: tuple[Celestial, Celestial, Celestial]
) -> list[Vec2]:
    """ Lock on the asteroid, then return on each frame the distance to it
    and the angle between the ship and the planet, seen from the asteroid """
    sun, planet, asteroid = system
    station = Station(asteroid, ship.position, MINING_DISTANCE)
    frames = []
    for _ in range(round(seconds / DT)):
        for celestial in (planet, asteroid):
            assert celestial.orbit
            celestial.orbit.advance(DT)
        ship.hold(DT, station, [sun, planet])
        body.step(DT)
        (x, y), (ax, ay), (px, py) = ship.position, asteroid.pos, planet.pos
        angle = math.atan2(y - ay, x - ax) - math.atan2(py - ay, px - ax)
        frames.append((math.dist((x, y), (ax, ay)), angle))
    return frames


def outside_of_the_belt(
    system: tuple[Celestial, Celestial, Celestial],
    distance: float
) -> Vec2:
    """ Point beyond the asteroid, on the line from its planet """
    _, planet, asteroid = system
    (px, py), (ax, ay) = planet.pos, asteroid.pos
    gap = math.dist((px, py), (ax, ay))
    return (
        ax + (ax - px) / gap * distance,
        ay + (ay - py) / gap * distance,
    )


def test_locked_ship_holds_in_front_of_its_target() -> None:
    system = make_belt()
    asteroid = system[2]
    ship, body = make_ship(
        position=outside_of_the_belt(system, 500.), velocity=asteroid.velocity
    )
    distances = [d for d, _ in hold(ship, body, 6., system)]
    assert distances[-1] == pytest.approx(MINING_DISTANCE, abs=2.)
    tx, ty = asteroid.pos
    x, y = ship.position
    assert abs(angle_diff(body.angle, math.atan2(ty - y, tx - x))) < .05


def test_locked_ship_does_not_overshoot_towards_its_target() -> None:
    # Overshooting could make it hit the asteroid
    system = make_belt()
    ship, body = make_ship(position=outside_of_the_belt(system, 900.))
    distances = [d for d, _ in hold(ship, body, 8., system)]
    assert min(distances) > MINING_DISTANCE - 5.


def test_locked_ship_follows_its_target_in_formation() -> None:
    # Once there, it keeps its place relative to the orbit of the asteroid
    system = make_belt()
    ship, body = make_ship(
        position=outside_of_the_belt(system, 500.), velocity=system[2].velocity
    )
    frames = hold(ship, body, 20., system)[round(5 / DT):]
    distances = [d for d, _ in frames]
    assert max(distances) - min(distances) < 2.
    angles = [a for _, a in frames]
    assert max(abs(angle_diff(a, angles[0])) for a in angles) < .02
    # Locked from outside of the belt, it never gets closer to the planet
    assert all(abs(angle_diff(a, math.pi)) < .05 for a in angles)


def test_locked_ship_stays_in_laser_range() -> None:
    system = make_belt()
    asteroid = system[2]
    ship, body = make_ship(
        position=outside_of_the_belt(system, 500.), velocity=asteroid.velocity
    )
    hold(ship, body, 6., system)
    assert math.dist(ship.nose, asteroid.pos) < LASER_RANGE


def test_a_ship_placed_stands_as_told() -> None:
    ship = Ship(1, FakeBody(), STATS)
    pose = Pose((10., 20.), (3., 4.), 1.)
    ship.place(pose)
    assert ship.pose == pose
