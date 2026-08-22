import pytest

from app.logic.world.chart import MARGIN, ZOOMS, chart, zoomed


def test_the_sun_is_in_the_middle() -> None:
    frame = chart((5000., 3000.), 10000., (640., 360.), (1280., 720.))
    assert frame.place((5000., 3000.)) == (640., 360.)


def test_the_farthest_orbit_fits_the_frame() -> None:
    frame = chart((0., 0.), 10000., (640., 360.), (1280., 720.))
    x, y = frame.place((0., 10000.))
    assert x == 640.
    assert y == pytest.approx(360. + 360. * MARGIN)
    assert frame.place((-10000., 0.))[0] > 0


def test_small_things_stay_seen() -> None:
    frame = chart((0., 0.), 10000., (0., 0.), (1000., 1000.))
    assert frame.size(200.) == pytest.approx(200. * 500 * MARGIN / 10000)
    assert frame.size(10., smallest=4.) == 4.


def test_zoomed_in_on_the_ship() -> None:
    whole = chart((0., 0.), 10000., (500., 500.), (1000., 1000.))
    closer = chart((0., 0.), 10000., (500., 500.), (1000., 1000.),
                   zoom=4., ship=(3000., 0.))
    assert closer.place((3000., 0.)) == (500., 500.)
    assert closer.scale == 4 * whole.scale


def test_zooms_stop_at_either_end() -> None:
    assert zoomed(ZOOMS[0], closer=True) == ZOOMS[1]
    assert zoomed(ZOOMS[0], closer=False) == ZOOMS[0]
    assert zoomed(ZOOMS[-1], closer=True) == ZOOMS[-1]
