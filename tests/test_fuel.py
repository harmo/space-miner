import pytest

from app.logic.ship.config import MIN_BURN
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
    scout = HULLS['scout'].burn
    assert ship_stats(Design()).burn == scout
    assert burn('afterburner') > burn('engine') > scout
    assert burn('ion_engine') < scout


def test_a_solar_sail_burns_little_but_never_nothing() -> None:
    sail = ship_stats(Design(parts={'rear': 'solar_sail'})).burn
    assert 0 < sail < ship_stats(Design()).burn


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
    gauges = [tank.state]
    for amount in (80., 15., 50.):
        tank.burn(amount)
        gauges.append(tank.state)
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


@pytest.mark.parametrize('hull_id', HULLS)
def test_nothing_makes_thrust_free(hull_id: str) -> None:
    rears = [
        slot for slot, kind in HULLS[hull_id].slots.items()
        if kind.kind == 'rear'
    ]
    stats = ship_stats(Design(hull_id, dict.fromkeys(rears, 'solar_sail')))
    assert stats.burn >= HULLS[hull_id].burn * MIN_BURN > 0


def test_the_bigger_the_hull_the_more_it_burns() -> None:
    burns = [HULLS[hull].burn
             for hull in ('scout', 'driller', 'hauler', 'cruiser')]
    assert burns == sorted(burns)
