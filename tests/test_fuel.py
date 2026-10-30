import pytest

from app.logic.ship.config import HULL_BURN
from app.logic.ship.fuel import Tank, burn_rate
from app.logic.ship.hulls import HULLS
from app.logic.ship.lasers import LASERS
from app.logic.ship.parts import PARTS
from app.logic.ship.shipyard import Design, ship_stats


def test_every_hull_has_a_tank() -> None:
    assert all(hull.tank > 0 for hull in HULLS.values())
    assert ship_stats(Design()).tank == HULLS['scout'].tank


def test_tanks_add_to_the_hull_s() -> None:
    design = Design('hauler', {
        'internal_1': 'fuel_tank', 'internal_2': 'large_tank',
    })
    expected = (
        HULLS['hauler'].tank + PARTS['fuel_tank'].tank
        + PARTS['large_tank'].tank
    )
    assert ship_stats(design).tank == expected


def test_engines_change_what_the_hull_burns() -> None:
    def burn(engine: str) -> float:
        return ship_stats(Design(parts={'rear': engine})).burn
    assert ship_stats(Design()).burn == HULL_BURN
    assert burn('afterburner') > burn('engine') > HULL_BURN
    assert burn('ion_engine') < HULL_BURN


def test_a_solar_sail_flies_for_free() -> None:
    assert ship_stats(Design(parts={'rear': 'solar_sail'})).burn == 0.


def test_better_lasers_burn_more() -> None:
    burns = [laser.burn for laser in LASERS]
    assert burns == sorted(burns) and burns[0] > 0


def test_fuel_burns_as_much_as_the_ship_thrusts_and_fires() -> None:
    stats = ship_stats(Design())
    assert burn_rate(stats, 0., False) == 0.
    assert burn_rate(stats, 1., False) == stats.burn
    assert burn_rate(stats, .3, False) == pytest.approx(.3 * stats.burn)
    assert burn_rate(stats, 0., True) == LASERS[0].burn


def test_a_tank_empties_and_fills_within_its_capacity() -> None:
    tank = Tank(100.)
    assert tank.share == 1.
    gauges = [tank.gauge]
    for amount in (80., 15., 50.):
        tank.burn(amount)
        gauges.append(tank.gauge)
    assert gauges == ['full', 'low', 'critical', 'empty']
    assert tank.empty and tank.level == 0. and tank.missing == 100.
    tank.fill(300.)
    assert tank.level == 100.


def test_a_smaller_tank_holds_less() -> None:
    tank = Tank(160.)
    tank.resize(100.)
    assert tank.level == 100.
    tank.resize(200.)
    assert tank.level == 100. and tank.missing == 100.
