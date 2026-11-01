from random import Random

import pytest

from app.logic.base.config import DEPOT_CAPACITY, MINE_RATE
from app.logic.base.mine import Mine
from app.logic.base.outposts import bare_outpost
from app.logic.base.post import Docked, Post, Services
from app.logic.base.sites import ARES, FRONTIER, ICARE
from app.logic.base.wallet import Wallet
from app.logic.ship.fuel import Tank
from app.logic.ship.heat import HullHeat
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


def test_a_mine_stops_when_the_depot_is_full() -> None:
    stock = {'rock': DEPOT_CAPACITY - 3.}
    mine = Mine(Random(3))
    mine.update(stock, 100 / MINE_RATE)
    assert sum(stock.values()) == DEPOT_CAPACITY
    mine.update(stock, 100 / MINE_RATE)
    assert sum(stock.values()) == DEPOT_CAPACITY


def test_a_full_mine_gets_going_again_once_there_is_room() -> None:
    stock = {'rock': float(DEPOT_CAPACITY)}
    mine = Mine(Random(7))
    mine.update(stock, 100 / MINE_RATE)
    assert mine.dug == 0.
    stock['rock'] -= 5.
    mine.update(stock, 5 / MINE_RATE)
    assert sum(stock.values()) == DEPOT_CAPACITY


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


def test_ares_digs_metals_and_dust_and_trades_nothing() -> None:
    stock: dict[str, float] = {}
    Mine(Random(8), ARES.yields).update(stock, 900 / MINE_RATE)
    assert set(stock) == {'iron', 'copper', 'regolith'}
    assert stock['iron'] > stock['copper'] > stock['regolith']
    final = ARES.stages[-1].services
    assert final.mine and final.depot and not final.market
    assert not ARES.gives_missions


def test_an_outpost_digs_what_its_site_yields() -> None:
    outpost = bare_outpost('ares', Celestial(1, 165.), Random(9))
    assert outpost.post.mine.yields == ARES.yields
