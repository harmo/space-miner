import math

import pytest

from app.logic.ship.config import (
    LANDED_GAP,
    LANDED_SPEED,
    LANDING_RANGE,
    LEG_LENGTH,
    SHORTCUT_RANGE,
)
from app.logic.ship.landing import (
    Ground,
    closest_spot,
    ground_gap,
    ground_margin,
    ground_spots,
    is_landed,
    landed_distance,
    landed_on,
    nearest,
    over_ground,
    pad_edge,
    parking_at,
    parking_on,
    shortcut,
    shortcut_text,
    surface_distance,
)
from app.logic.ship.pose import Pose
from app.logic.world.space import Celestial

from .worlds import SHIP_LENGTH, SHIP_WIDTH, SIZE, around, earth

# Ground

def test_landed_on_a_planet() -> None:
    planet = Celestial(0, 200., pos=(1000., 500.))
    x, y = landed_on(planet, -math.pi / 2, SHIP_LENGTH)
    assert (x, y) == pytest.approx(
        (1000., 500. - 200. - SHIP_LENGTH / 2 - LEG_LENGTH)
    )


def test_ship_fits_inside_ground_spots() -> None:
    ground = [10 <= degrees <= 30 for degrees in range(360)]
    spots = [round(math.degrees(spot)) for spot in ground_spots(ground, 3)]
    assert spots == list(range(13, 28))


def test_ground_spots_across_the_east() -> None:
    ground = [degrees >= 350 or degrees <= 10 for degrees in range(360)]
    spots = [round(math.degrees(spot)) for spot in ground_spots(ground, 2)]
    assert spots == [*range(0, 9), *range(352, 360)]


def test_no_ground_no_spot() -> None:
    assert ground_spots([False] * 360, 1) == []


def test_margin_covers_half_the_ship_width() -> None:
    planet = earth()
    half_width = math.degrees(SHIP_WIDTH / 2 / planet.radius)
    assert half_width < ground_margin(planet, SHIP_WIDTH) < half_width + 10


def test_closest_spot_goes_across_the_east() -> None:
    spots = [math.radians(10), math.radians(200)]
    assert closest_spot(math.radians(355), spots) == math.radians(10)
    assert closest_spot(math.radians(150), spots) == math.radians(200)


def test_without_spots_any_direction_does() -> None:
    assert closest_spot(1.2, []) == 1.2


# Shortcut

def test_shortcut_shows_up_then_can_be_used() -> None:
    assert shortcut(SHORTCUT_RANGE * 2, False, ground=True) == 'hidden'
    middle = (SHORTCUT_RANGE + LANDING_RANGE) / 2
    assert shortcut(middle, False, ground=True) == 'far'
    assert shortcut(LANDING_RANGE / 2, False, ground=True) == 'ready'
    assert shortcut(0., landed=True, ground=True) == 'hidden'


def test_shortcut_needs_ground_below() -> None:
    assert shortcut(LANDING_RANGE / 2, False, ground=False) == 'aside'
    middle = (SHORTCUT_RANGE + LANDING_RANGE) / 2
    assert shortcut(middle, False, ground=False) == 'far'


def test_over_ground_right_above_a_spot() -> None:
    spots = [math.radians(degrees) for degrees in range(10, 31)]
    assert over_ground(math.radians(20.3), spots)
    assert over_ground(math.radians(30.4), spots)
    assert not over_ground(math.radians(32), spots)
    assert not over_ground(math.radians(200), spots)
    assert not over_ground(0., [])


def test_landed_ship() -> None:
    planet = earth()
    direction = 1.
    position = landed_on(planet, direction, SHIP_LENGTH)
    assert surface_distance(position, planet) < SHIP_LENGTH
    assert is_landed(Pose(position, planet.velocity, direction), planet, SIZE)
    vx, vy = planet.velocity
    assert not is_landed(
        Pose(position, (vx, vy + LANDED_SPEED * 2), direction), planet, SIZE
    )
    assert not is_landed(
        Pose(around(planet, 0, 1000.), planet.velocity, 0.), planet, SIZE
    )


def test_hovering_ship_is_not_landed() -> None:
    planet = earth()
    position = around(planet, 90, landed_distance(planet, SHIP_LENGTH) + 13.)
    assert not is_landed(
        Pose(position, planet.velocity, math.pi / 2), planet, SIZE
    )


def test_ship_lies_lower_on_its_side() -> None:
    planet = earth()
    nose_up = around(planet, 90, planet.radius + SHIP_LENGTH / 2)
    assert ground_gap(nose_up, math.pi / 2, planet, SIZE) == (
        pytest.approx(0.)
    )
    on_its_side = around(planet, 90, planet.radius + SHIP_WIDTH / 2)
    assert ground_gap(on_its_side, 0., planet, SIZE) == pytest.approx(0.)
    # On its side at the height of a ship on its nose, it hovers
    assert ground_gap(nose_up, 0., planet, SIZE) > LANDED_GAP


# Parking

def test_parked_ship_moves_along_with_its_planet() -> None:
    planet = earth()
    assert planet.orbit
    direction = math.radians(30)
    parking = parking_on(planet, direction, SHIP_LENGTH)
    before = parking.position
    assert before == pytest.approx(landed_on(planet, direction, SHIP_LENGTH))
    planet.orbit.advance(60.)
    after = parking.position
    assert after != pytest.approx(before)
    assert after == pytest.approx(landed_on(planet, direction, SHIP_LENGTH))


def test_parked_ship_knows_what_it_is_parked_on() -> None:
    planet = earth()
    assert parking_on(planet, 0., SHIP_LENGTH).body is planet


def test_parked_ship_keeps_how_it_landed() -> None:
    planet = earth()
    pos = around(planet, 200, 215.)          # lying on its side
    parking = parking_at(planet, Pose(pos, (0., 0.), 1.))
    assert parking.position == pytest.approx(pos)
    assert parking.angle == 1.
    assert parking.pose.velocity == planet.velocity


# Grounds, of the bodies ships land on

def test_a_ground_tells_where_ships_fit() -> None:
    planet = Celestial(0, 200.)
    edge = tuple(10 <= degree <= 30 for degree in range(360))
    ground = Ground(planet, edge)
    margin = ground_margin(planet, SHIP_WIDTH)
    assert ground.spots(SHIP_WIDTH) == ground_spots(list(edge), margin)
    assert ground.spots(SHIP_WIDTH)


def test_the_nearest_ground_is_that_of_the_closest_surface() -> None:
    small = Ground(Celestial(1, 50., pos=(0., 0.)), (True,) * 360)
    big = Ground(Celestial(2, 400., pos=(1000., 0.)), (True,) * 360)
    assert nearest([small, big], (480., 0.)) is big
    assert nearest([small, big], (300., 0.)) is small


def test_a_pad_is_ground_around_its_direction_only() -> None:
    edge = pad_edge(200., math.radians(90), 100.)
    half = math.degrees(50. / 200.)
    assert edge[90] and edge[90 + int(half)] and edge[90 - int(half)]
    assert not edge[90 + int(half) + 1] and not edge[270]
    assert sum(edge) == pytest.approx(2 * half, abs=1.5)


def test_a_pad_across_the_east() -> None:
    edge = pad_edge(100., 0., 60.)
    assert edge[0] and edge[359] and edge[10] and not edge[180]


def test_the_shortcut_tells_what_it_is_aside_from() -> None:
    assert shortcut_text('aside', 'land') == "Au-dessus de l'eau"
    assert shortcut_text('aside', 'pad') == 'Hors de la plateforme'
    assert shortcut_text('aside', 'port') == 'Hors du port'


def test_the_shortcut_lands_or_docks() -> None:
    assert shortcut_text('ready', 'land') == 'Atterrir'
    assert shortcut_text('far', 'pad') == 'Atterrir'
    assert shortcut_text('ready', 'port') == "S'amarrer"
