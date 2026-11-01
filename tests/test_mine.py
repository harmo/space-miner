import math
from random import Random

import pytest

from app.logic.base.config import (
    DEPOT_CAPACITY,
    MINE_RATE,
    SHUTTLE_LOAD,
    SHUTTLE_SPEED,
    SHUTTLE_SUN_CLEARANCE,
)
from app.logic.base.mine import Mine
from app.logic.base.outposts import bare_outpost
from app.logic.base.post import Docked, Post, Services
from app.logic.base.sites import ARES, FRONTIER, ICARE
from app.logic.base.wallet import Wallet
from app.logic.ship.fuel import Tank
from app.logic.ship.heat import HullHeat
from app.logic.world.config import MARS_ORBIT, SUN_RADIUS
from app.logic.world.layout import plan_system, sun_belt_orbit
from app.logic.world.space import Celestial


def test_a_mine_digs_slowly() -> None:
    mine = Mine(Random(1))
    stock: dict[str, float] = {}
    mine.update(stock, .9 / MINE_RATE)
    assert not stock
    mine.update(stock, .2 / MINE_RATE)
    assert sum(stock.values()) == 1.


def test_a_mine_digs_mostly_helium() -> None:
    stock: dict[str, float] = {}
    Mine(Random(2)).update(stock, 800 / MINE_RATE)
    assert sum(stock.values()) == 800.
    assert stock['helium3'] == pytest.approx(3 * stock['ice'], rel=.1)


def full_of(capacity: float = DEPOT_CAPACITY) -> dict[str, float]:
    return {'helium3': capacity, 'ice': capacity}


def test_a_mine_stops_when_the_depot_has_no_room_for_what_it_digs() -> None:
    stock = full_of(DEPOT_CAPACITY - 2.)
    mine = Mine(Random(3))
    mine.update(stock, 100 / MINE_RATE)
    assert stock == full_of()
    mine.update(stock, 100 / MINE_RATE)
    assert stock == full_of()


def test_a_mine_goes_on_with_what_still_has_room() -> None:
    stock = {'helium3': float(DEPOT_CAPACITY)}
    Mine(Random(10)).update(stock, 50 / MINE_RATE)
    assert stock == {'helium3': DEPOT_CAPACITY, 'ice': 50.}


def test_other_minerals_do_not_stop_a_mine() -> None:
    stock = {'rock': float(DEPOT_CAPACITY)}
    Mine(Random(11)).update(stock, 10 / MINE_RATE)
    assert sum(stock.values()) == DEPOT_CAPACITY + 10.


def test_a_full_mine_gets_going_again_once_there_is_room() -> None:
    stock = full_of()
    mine = Mine(Random(7))
    mine.update(stock, 100 / MINE_RATE)
    assert mine.dug == 0.
    stock['ice'] -= 5.
    mine.update(stock, 5 / MINE_RATE)
    assert stock == full_of()


def test_a_mine_digs_with_no_ship_around() -> None:
    post = Post(Services(depot=True, mine=True), Random(4))
    post.update(10 / MINE_RATE, None, Wallet())
    assert sum(post.depot.stock.values()) == 10.


def test_no_digging_without_a_mine() -> None:
    post = Post(Services(depot=True), Random(5))
    post.update(10 / MINE_RATE, None, Wallet())
    assert not post.depot.stock


def test_a_mine_digs_while_a_ship_is_there() -> None:
    post = Post(Services(depot=True, mine=True), Random(6))
    ship = Docked({}, Tank(100.), HullHeat())
    post.update(10 / MINE_RATE, ship, Wallet())
    assert sum(post.depot.stock.values()) == 10.


def test_only_the_frontier_ends_with_a_mine() -> None:
    assert FRONTIER.stages[-1].services.mine
    assert not ICARE.stages[-1].services.mine


def longest_way_from_neptune(seed: int) -> float:
    """ In pixels, to the farthest post with a depot, the sun in between """
    plan = plan_system(Random(seed))
    neptune = plan.planets[-1].planet.orbit_radius
    farthest = max(
        plan.planets[MARS_ORBIT].planet.orbit_radius,
        sun_belt_orbit(plan.orbits),
    )
    around = SUN_RADIUS + SHUTTLE_SUN_CLEARANCE
    return neptune + farthest + 2 * around * (math.pi / 2 - 1)


def test_the_frontier_never_digs_more_than_its_shuttle_carries() -> None:
    longest = max(longest_way_from_neptune(seed) for seed in range(300))
    round_trip = 2 * longest / SHUTTLE_SPEED
    assert round_trip * FRONTIER.vein.rate < SHUTTLE_LOAD


def test_ares_digs_a_shuttle_every_five_minutes() -> None:
    assert ARES.vein.rate * 300. == pytest.approx(SHUTTLE_LOAD)


def test_ares_digs_metals_and_dust_and_trades_nothing() -> None:
    stock: dict[str, float] = {}
    Mine(Random(8), ARES.vein).update(stock, 900 / ARES.vein.rate)
    assert set(stock) == {'iron', 'copper', 'regolith'}
    assert stock['iron'] > stock['copper'] > stock['regolith']
    final = ARES.stages[-1].services
    assert final.mine and final.depot and not final.market
    assert not ARES.gives_missions


def test_an_outpost_digs_what_its_site_yields() -> None:
    outpost = bare_outpost('ares', Celestial(1, 165.), Random(9))
    assert outpost.post.mine.vein == ARES.vein
