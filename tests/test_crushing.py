from random import Random

import pytest

from app.logic.base.config import CRUSH_RATE, CRUSH_YIELDS
from app.logic.base.crushing import Crusher, sift


def test_nothing_to_crush_without_rock() -> None:
    crusher = Crusher(Random(1))
    crusher.start({'iron': 10.})
    assert not crusher.crushing
    assert crusher.update({'iron': 10.}, 1.) == []


def test_rock_is_crushed_a_bit_at_a_time() -> None:
    crusher = Crusher(Random(2))
    stock = {'rock': 100.}
    crusher.start(stock)
    crusher.update(stock, 1.)
    assert stock['rock'] == pytest.approx(100. - CRUSH_RATE)
    assert crusher.crushing


def test_until_none_is_left() -> None:
    crusher = Crusher(Random(3))
    stock = {'rock': 10.}
    crusher.start(stock)
    found = crusher.update(stock, 100.)
    assert 'rock' not in stock and not crusher.crushing
    assert sum(stock.values()) == len(found) == 10


def test_crushed_rock_gives_other_ore_now_and_then() -> None:
    crusher = Crusher(Random(4))
    stock = {'rock': 10000.}
    crusher.start(stock)
    found = crusher.update(stock, 10000. / CRUSH_RATE)
    for mineral, chance in CRUSH_YIELDS:
        assert found.count(mineral) == pytest.approx(10000 * chance, rel=.2)
        assert stock[mineral] == found.count(mineral)


def test_most_of_it_is_regolith() -> None:
    rng = Random(5)
    regolith = sum(sift(rng) == 'regolith' for _ in range(1000))
    assert regolith > 400
