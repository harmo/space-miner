import pytest

from app.logic.base.config import UNLOAD_RATE
from app.logic.base.unloading import Depot, unload


def test_unloads_one_mineral_after_the_other() -> None:
    ore = {'gold': 3., 'rock': 5.}
    stock: dict[str, float] = {}
    assert unload(ore, stock, 4.) == 'rock'
    assert ore == {'gold': 3., 'rock': 1.}
    assert unload(ore, stock, 4.) == 'rock'
    assert ore == {'gold': 3.}
    assert unload(ore, stock, 4.) == 'gold'
    assert ore == {}
    assert stock == {'rock': 5., 'gold': 3.}
    assert unload(ore, stock, 4.) is None


def test_stock_adds_up() -> None:
    stock = {'ice': 10.}
    unload({'ice': 2.}, stock, 5.)
    assert stock == {'ice': 12.}


def test_depot_empties_the_cargo_over_time() -> None:
    depot = Depot()
    ore = {'iron': UNLOAD_RATE * 2}
    depot.start(ore)
    depot.update(ore, 1., docked=True)
    assert depot.mineral == 'iron'
    assert ore['iron'] == pytest.approx(UNLOAD_RATE)
    depot.update(ore, 1.5, docked=True)
    assert ore == {}
    depot.update(ore, .1, docked=True)
    assert not depot.unloading
    assert depot.stock == {'iron': pytest.approx(UNLOAD_RATE * 2)}


def test_taking_off_stops_unloading() -> None:
    depot = Depot()
    ore = {'iron': 10.}
    depot.start(ore)
    depot.update(ore, .1, docked=False)
    assert not depot.unloading and depot.mineral is None
    assert ore == {'iron': 10.}


def test_nothing_to_unload() -> None:
    depot = Depot()
    depot.start({})
    assert not depot.unloading
