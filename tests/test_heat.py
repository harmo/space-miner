import pytest

from app.logic.config import HEAT_RANGE
from app.logic.ship.config import HEAT_COOLING, HEAT_GAIN, HOT, OVERHEATING
from app.logic.ship.heat import Hull, Sunlight, heating


def test_the_sun_heats_more_and_more_closer() -> None:
    assert heating(HEAT_RANGE) == 0.
    assert heating(0.) == HEAT_GAIN
    assert 0. < heating(HEAT_RANGE / 2) < HEAT_GAIN / 2


def test_shields_stop_part_of_the_heat_and_flares_add_to_it() -> None:
    assert heating(0., shield=.75) == pytest.approx(HEAT_GAIN / 4)
    assert heating(0., surge=3.) == pytest.approx(HEAT_GAIN * 3)


def test_the_hull_heats_up_and_cools_down() -> None:
    hull = Hull()
    hull.update(1., heating(0.))
    assert hull.heat == pytest.approx(HEAT_GAIN - HEAT_COOLING)
    hull.update(100., 0.)
    assert hull.heat == 0.


def test_too_hot_the_hull_is_burnt() -> None:
    hull = Hull()
    warmths = [hull.warmth]
    for heat in (HOT, OVERHEATING):
        hull.heat = heat
        warmths.append(hull.warmth)
    assert warmths == ['cool', 'hot', 'overheating']
    assert not hull.burnt
    hull.update(100., heating(0.))
    assert hull.burnt and hull.heat == 1.
    hull.cool()
    assert hull.heat == 0.


def test_sunlight_tells_how_far_from_the_sun_surface() -> None:
    sunlight = Sunlight((100., 0.), 50., surge=2.)
    assert sunlight.distance((100., 300.)) == 250.
    assert sunlight.surge == 2.
