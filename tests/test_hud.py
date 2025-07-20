import math
from itertools import pairwise

import pytest

from app.logic.config import (
    CARGO_ALMOST_FULL_COLOR,
    CARGO_COLOR,
    CARGO_FULL_COLOR,
    MARKER_FAR,
    MARKER_LENGTH,
    MARKER_NEAR,
)
from app.logic.hud import (
    cargo_color,
    edge_point,
    is_compact,
    is_on_screen,
    marker_length,
    orbit_dots,
    pulse,
)
from app.logic.world.space import Vec2

HALF_SIZE = (960., 540.)


@pytest.mark.parametrize('direction, point, on_side', [
    (0., (960., 0.), True),
    (math.pi, (-960., 0.), True),
    (math.pi / 2, (0., 540.), False),
    (-math.pi / 2, (0., -540.), False),
])
def test_edge_point_straight(direction: float, point: Vec2,
                             on_side: bool) -> None:
    (x, y), side = edge_point(direction, HALF_SIZE)
    assert (x, y) == pytest.approx(point, abs=1e-9)
    assert side == on_side


def test_edge_point_diagonal_hits_the_closest_edge() -> None:
    # 45° hits the top edge first on a wide screen
    (x, y), on_side = edge_point(math.pi / 4, HALF_SIZE)
    assert (x, y) == pytest.approx((540., 540.))
    assert not on_side


def test_edge_point_is_on_the_screen_border() -> None:
    for degrees in range(0, 360, 7):
        (x, y), on_side = edge_point(math.radians(degrees), HALF_SIZE)
        assert abs(x) <= HALF_SIZE[0] + 1e-9
        assert abs(y) <= HALF_SIZE[1] + 1e-9
        border = abs(x) if on_side else abs(y)
        assert border == pytest.approx(HALF_SIZE[0 if on_side else 1])


def test_markers_grow_as_targets_get_closer() -> None:
    shortest, longest = MARKER_LENGTH
    assert marker_length(MARKER_FAR * 2) == shortest
    assert marker_length(MARKER_NEAR / 2) == longest
    lengths = [marker_length(d) for d in range(0, 30000, 500)]
    assert lengths == sorted(lengths, reverse=True)


def test_target_on_screen() -> None:
    assert is_on_screen((0., 0.), 10., HALF_SIZE)
    assert is_on_screen((1000., 0.), 100., HALF_SIZE)   # partly visible
    assert not is_on_screen((1100., 0.), 100., HALF_SIZE)
    assert not is_on_screen((0., -700.), 100., HALF_SIZE)


# Orbits

VIEW = (960., 540.)


def test_no_dots_for_an_orbit_out_of_view() -> None:
    assert orbit_dots((0., 0.), 5000., (0., 0.), VIEW, 14.) == []
    assert orbit_dots((0., 0.), 5000., (9000., 0.), VIEW, 14.) == []


def test_dots_are_on_the_orbit_and_in_view() -> None:
    view_center = (5000., 300.)
    dots = orbit_dots((0., 0.), 5000., view_center, VIEW, 14.)
    assert len(dots) > 50
    for x, y in dots:
        assert math.hypot(x, y) == pytest.approx(5000.)
        assert abs(x - view_center[0]) <= VIEW[0]
        assert abs(y - view_center[1]) <= VIEW[1]


def test_dots_are_evenly_spaced() -> None:
    dots = orbit_dots((0., 0.), 5000., (0., 5000.), VIEW, 14.)
    gaps = [math.dist(a, b) for a, b in pairwise(sorted(dots))]
    assert min(gaps) == pytest.approx(14., rel=.01)
    assert max(gaps) == pytest.approx(14., rel=.01)


def test_dots_do_not_slide_as_the_view_moves() -> None:
    before = orbit_dots((0., 0.), 5000., (5000., 0.), VIEW, 14.)
    after = orbit_dots((0., 0.), 5000., (5000., 37.), VIEW, 14.)
    common = set(before) & set(after)
    assert len(common) > len(before) * .8


def test_small_orbit_in_view_is_complete() -> None:
    dots = orbit_dots((0., 0.), 200., (0., 0.), VIEW, 14.)
    assert len(dots) == round(2 * math.pi * 200. / 14.)
    assert len(set(dots)) == len(dots)


def test_no_dots_over_the_planet() -> None:
    planet = (5000., 0.)
    dots = orbit_dots(
        (0., 0.), 5000., planet, VIEW, 14., hidden=(planet, 250.)
    )
    assert dots
    assert all(math.dist(dot, planet) >= 250. for dot in dots)


# Compact interface

def test_compact_interface_on_mobile_platforms() -> None:
    assert is_compact('android', 2000., 1200.)
    assert is_compact('ios', 2000., 1200.)


def test_compact_interface_on_small_screens() -> None:
    assert is_compact('linux', 800., 360.)       # phone in landscape
    assert not is_compact('linux', 1920., 1080.)
    assert not is_compact('win', 1024., 768.)    # small laptop


# Cargo

def test_cargo_bar_warns_when_almost_full_then_full() -> None:
    assert cargo_color(0.) == CARGO_COLOR
    assert cargo_color(.5) == CARGO_COLOR
    assert cargo_color(.95) == CARGO_ALMOST_FULL_COLOR
    assert cargo_color(1.) == CARGO_FULL_COLOR


def test_pulse_goes_smoothly_back_and_forth() -> None:
    assert pulse(0., 2.) == pytest.approx(0.)
    assert pulse(1., 2.) == pytest.approx(1.)
    assert pulse(2., 2.) == pytest.approx(0., abs=1e-12)
    assert all(0. <= pulse(t / 10, 2.) <= 1. for t in range(100))
