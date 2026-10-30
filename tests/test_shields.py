import pytest

from app.logic.ship.config import REGOLITH_TINT
from app.logic.ship.parts import PARTS, effects
from app.logic.ship.shipyard import Design, shielding, ship_stats, tint


def test_no_shield_lets_all_the_heat_through() -> None:
    assert ship_stats(Design()).shield == 0.
    assert tint(Design()) == (1., 1., 1.)


def test_a_shield_stops_its_part_of_the_heat() -> None:
    design = Design(parts={'internal': 'regolith_shield'})
    assert ship_stats(design).shield == PARTS['regolith_shield'].shield


def test_shields_stop_what_the_others_let_through() -> None:
    assert shielding([.5, .75]) == pytest.approx(1 - .5 * .25)
    design = Design('hauler', {
        'internal_1': 'regolith_shield', 'internal_2': 'heavy_shield',
    })
    assert ship_stats(design).shield == pytest.approx(.875)


def test_shielded_ships_take_the_color_of_regolith() -> None:
    light = tint(Design(parts={'internal': 'regolith_shield'}))
    heavy = tint(Design(parts={'internal': 'heavy_shield'}))
    assert all(r < 1 for r in light)
    assert all(h < r for h, r in zip(heavy, light, strict=True))
    assert all(h > t for h, t in zip(heavy, REGOLITH_TINT, strict=True))


def test_shields_are_made_of_regolith() -> None:
    for part in ('regolith_shield', 'heavy_shield'):
        assert dict(PARTS[part].materials)['regolith'] > 0
    assert effects(PARTS['regolith_shield']) == '+50% bouclier thermique'
