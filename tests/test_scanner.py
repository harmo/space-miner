import pytest

from app.logic.config import CHEVRON_OPACITY, CHEVRON_SIZE
from app.logic.hud import chevron_look
from app.logic.ship.scanner import LOOKED_FOR, counts, found, within
from app.logic.world.space import Celestial


def asteroid(entity_id: int, x: float, mineral: str | None) -> Celestial:
    return Celestial(entity_id, 5., pos=(x, 0.), mineral=mineral)


ASTEROIDS = [
    asteroid(1, 3000., 'gold'),
    asteroid(2, 500., None),
    asteroid(3, 1200., 'gold'),
    asteroid(4, 800., 'iron'),
]


def test_finds_what_is_within_reach_closest_first() -> None:
    ids = [rock.entity_id for rock in within(ASTEROIDS, (0., 0.), 1500.)]
    assert ids == [2, 4, 3]


def test_finds_only_the_minerals_looked_for() -> None:
    gold = found(ASTEROIDS, (0., 0.), 5000., {'gold'}, 10)
    assert [rock.entity_id for rock in gold] == [3, 1]
    assert len(found(ASTEROIDS, (0., 0.), 5000., {'gold'}, 1)) == 1
    assert found(ASTEROIDS, (0., 0.), 5000., set(), 10) == []


def test_counts_by_mineral() -> None:
    counted = counts(ASTEROIDS, (0., 0.), 1500.)
    assert counted['gold'] == 1 and counted['iron'] == 1
    assert counted['rock'] == 1
    assert counted['ruby'] == 0


def test_rock_is_not_looked_for_unless_asked() -> None:
    assert 'rock' not in LOOKED_FOR and 'gold' in LOOKED_FOR


def test_chevrons_grow_brighter_as_asteroids_get_closer() -> None:
    (smallest, biggest), (faint, bright) = CHEVRON_SIZE, CHEVRON_OPACITY
    assert chevron_look(4000., 4000.) == pytest.approx((smallest, faint))
    assert chevron_look(0., 4000.) == pytest.approx((biggest, bright))
    size, opacity = chevron_look(1000., 4000.)
    assert smallest < size < biggest and faint < opacity < bright
    assert chevron_look(100., 0.) == (smallest, faint)
    assert bright < 1                   # discreet even when close
