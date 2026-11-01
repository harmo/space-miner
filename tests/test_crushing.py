from random import Random

import pytest

from app.logic.base.config import CRUSH_RATE, CRUSH_YIELDS, DEPOT_CAPACITY
from app.logic.base.crushing import PLAIN_REFINERY, Crusher, Refinery, sift
from app.logic.base.sites import CERES, FRONTIER, ICARE


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
        assert stock[mineral] == min(found.count(mineral), DEPOT_CAPACITY)


def test_most_of_it_is_regolith() -> None:
    rng = Random(5)
    regolith = sum(sift(rng, CRUSH_YIELDS) == 'regolith' for _ in range(1000))
    assert regolith > 400


def test_a_refinery_sets_the_pace() -> None:
    crusher = Crusher(Random(6), Refinery(rate=12.))
    stock = {'rock': 100.}
    crusher.start(stock)
    crusher.update(stock, 1.)
    assert stock['rock'] == pytest.approx(88.)


def test_ceres_crushes_faster_and_richer_than_the_earth() -> None:
    refinery, earth = CERES.refinery, PLAIN_REFINERY
    assert refinery.rate == 3 * earth.rate
    rich, plain = dict(refinery.yields), dict(earth.yields)
    assert all(rich[name] >= chance for name, chance in plain.items())
    assert rich['gold'] > plain['gold'] and 'ruby' in rich
    assert sum(rich.values()) < 1.


def test_only_ceres_has_a_refinery_of_its_own() -> None:
    assert FRONTIER.refinery == ICARE.refinery == PLAIN_REFINERY


def test_crushing_keeps_within_the_limit_of_each_mineral() -> None:
    crusher = Crusher(Random(7), Refinery(yields=(('iron', 1.),)))
    stock = {'rock': 10., 'iron': DEPOT_CAPACITY - 4.}
    crusher.start(stock)
    crusher.update(stock, 100.)
    assert stock == {'iron': DEPOT_CAPACITY}
