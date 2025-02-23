import pytest

from app.logic.colors import rgb
from app.logic.mining.minerals import (
    GLOW_SCALE,
    MINERALS,
    display_scale,
    mining_rate,
)
from app.logic.ship.config import LASER_RATE
from app.logic.ship.hulls import HULLS

# Of the smallest ship, without any part
LASER_LEVEL = HULLS['scout'].laser


def test_harder_minerals_take_longer_to_mine() -> None:
    rock, gold = MINERALS['rock'], MINERALS['gold']
    assert mining_rate(rock, LASER_LEVEL, LASER_RATE) == LASER_RATE
    assert mining_rate(gold, LASER_LEVEL, LASER_RATE) < LASER_RATE / 2


def test_some_minerals_need_a_better_laser() -> None:
    out_of_reach = [
        mineral for mineral in MINERALS.values()
        if mining_rate(mineral, LASER_LEVEL, LASER_RATE) == 0
    ]
    assert out_of_reach
    for mineral in out_of_reach:
        assert mining_rate(mineral, mineral.laser, LASER_RATE) > 0


def test_every_mineral_can_be_found() -> None:
    assert all(mineral.frequency > 0 for mineral in MINERALS.values())


def test_colors() -> None:
    assert rgb('#ff8000') == pytest.approx((1., 128 / 255, 0.))
    for mineral in MINERALS.values():
        assert all(0 <= channel <= 1 for channel in mineral.color)


def test_names_with_their_article() -> None:
    for mineral in MINERALS.values():
        assert mineral.the.endswith(mineral.name.lower())
        assert mineral.the.startswith(('le ', 'la ', "l'"))


def test_better_lasers_open_new_minerals() -> None:
    levels = {mineral.laser for mineral in MINERALS.values()}
    assert levels == set(range(1, max(levels) + 1))


def test_glowing_minerals_have_bigger_images() -> None:
    assert display_scale(None) == 1.
    assert display_scale('rock') == 1.
    glowing = [name for name, m in MINERALS.items() if m.glow]
    assert glowing
    assert all(display_scale(name) == GLOW_SCALE for name in glowing)
