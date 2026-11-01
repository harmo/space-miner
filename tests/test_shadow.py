import math

from app.logic.ship.heat import Sunlight
from app.logic.world.config import SHADOW_LENGTH
from app.logic.world.shadow import shadow_of

SUN = (0., 0.)
PLANET = (2000., 0.)
RADIUS = 150.


def test_the_shadow_lies_away_from_the_sun() -> None:
    shadow = shadow_of(PLANET, RADIUS, SUN)
    assert shadow.tip == (2000. + SHADOW_LENGTH, 0.)
    assert shadow.covers((2300., 0.))
    assert not shadow.covers((1700., 0.))


def test_the_shadow_narrows_down() -> None:
    shadow = shadow_of(PLANET, RADIUS, SUN)
    assert shadow.covers((2100., 120.))
    assert not shadow.covers((2000. + SHADOW_LENGTH - 100., 120.))
    assert not shadow.covers((2000. + SHADOW_LENGTH + 10., 0.))


def test_the_shadow_turns_with_the_planet() -> None:
    angle = 2.
    pos = (2000. * math.cos(angle), 2000. * math.sin(angle))
    behind = (2300. * math.cos(angle), 2300. * math.sin(angle))
    shadow = shadow_of(pos, RADIUS, SUN)
    assert shadow.covers(behind)
    assert not shadow.covers((2300., 0.))


def test_sunlight_tells_what_is_shaded() -> None:
    light = Sunlight(SUN, 600., shadow=shadow_of(PLANET, RADIUS, SUN))
    assert light.shaded((2300., 0.))
    assert not light.shaded((2300., 400.))
    assert not Sunlight(SUN, 600.).shaded((2300., 0.))
