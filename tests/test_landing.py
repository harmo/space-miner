import math

import pytest

from app.logic.ship.ground import landed_distance, landed_on
from app.logic.ship.landing import Landing
from app.logic.ship.pose import Pose
from app.logic.ship.ship import is_crash
from app.logic.world.space import Celestial, Vec2, angle_diff

from .worlds import SHIP_LENGTH, around, earth

DURATION = 3.
STEPS = 300


def flying(position: Vec2, angle: float = 0.) -> Pose:
    return Pose(position, (0., 0.), angle)


def fly_landing(planet: Celestial, landing: Landing) -> list[float]:
    """ Distances to the planet center along the whole landing """
    assert planet.orbit
    distances = []
    while not landing.done:
        planet.orbit.advance(DURATION / STEPS)
        landing.advance(DURATION / STEPS)
        distances.append(math.dist(landing.position, planet.pos))
    return distances


def direction_from(planet: Celestial, pos: Vec2) -> float:
    x, y = planet.pos
    return math.atan2(pos[1] - y, pos[0] - x)


# Landing

def test_landing_starts_where_the_ship_is() -> None:
    planet = earth()
    start = around(planet, 30, 600.)
    landing = Landing(
        planet, flying(start), math.radians(30), SHIP_LENGTH, DURATION
    )
    assert landing.position == pytest.approx(start)
    assert landing.pose == Pose(
        landing.position, landing.velocity, landing.angle,
    )


@pytest.mark.parametrize('start_degrees, spot_degrees', [
    (30., 30.), (30., 100.), (170., -150.), (0., -90.),
])
def test_landing_ends_on_the_spot(
    start_degrees: float,
    spot_degrees: float
) -> None:
    planet = earth()
    spot = math.radians(spot_degrees)
    landing = Landing(
        planet, flying(around(planet, start_degrees, 600.)), spot,
        SHIP_LENGTH, DURATION,
    )
    fly_landing(planet, landing)
    assert landing.position == pytest.approx(
        landed_on(planet, spot, SHIP_LENGTH)
    )
    assert abs(angle_diff(landing.angle, spot)) < 1e-9


def test_landing_comes_down_steadily_and_never_inside() -> None:
    planet = earth()
    distances = fly_landing(planet, Landing(
        planet, flying(around(planet, 90, 900.)), math.radians(-20),
        SHIP_LENGTH, DURATION,
    ))
    assert distances == sorted(distances, reverse=True)
    assert min(distances) >= landed_distance(planet, SHIP_LENGTH) - 1e-9


def test_landing_goes_around_the_short_way() -> None:
    planet = earth()
    landing = Landing(
        planet, flying(around(planet, 170, 500.)), math.radians(-170),
        SHIP_LENGTH, DURATION,
    )
    directions = []
    while not landing.done:
        landing.advance(DURATION / STEPS)
        directions.append(direction_from(planet, landing.position))
    # From 170° to 190° through 180°, never through the east
    assert all(abs(d) > math.radians(160) for d in directions)


def test_landing_touches_down_softly() -> None:
    planet = earth()
    landing = Landing(
        planet, flying(around(planet, 180, 800.)), math.radians(120),
        SHIP_LENGTH, DURATION,
    )
    fly_landing(planet, landing)
    vx, vy = landing.velocity
    pvx, pvy = planet.velocity
    relative_speed = math.hypot(vx - pvx, vy - pvy)
    assert relative_speed == pytest.approx(0., abs=1e-9)
    assert not is_crash(relative_speed, landable=True)


def test_landing_velocity_matches_its_motion() -> None:
    planet = earth()
    assert planet.orbit
    landing = Landing(
        planet, flying(around(planet, -20, 540.)), math.radians(60),
        SHIP_LENGTH, DURATION,
    )
    landing.advance(1.)
    planet.orbit.advance(1.)
    before = landing.position
    velocity = landing.velocity
    landing.advance(1e-4)
    planet.orbit.advance(1e-4)
    after = landing.position
    moved = ((after[0] - before[0]) / 1e-4, (after[1] - before[1]) / 1e-4)
    assert moved == pytest.approx(velocity, rel=1e-3)


def test_nose_turns_the_short_way() -> None:
    planet = earth()
    # Nose up from slightly right of up: turning left would be the long way
    landing = Landing(
        planet, flying(around(planet, 90, 600.), math.pi / 2 - .2),
        math.pi / 2, SHIP_LENGTH, DURATION,
    )
    angles = []
    for _ in range(STEPS):
        landing.advance(DURATION / STEPS)
        angles.append(landing.angle)
    assert all(
        math.pi / 2 - .2 - 1e-9 <= a <= math.pi / 2 + 1e-9 for a in angles
    )
