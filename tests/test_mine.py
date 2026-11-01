from random import Random

import pytest

from app.logic.base.config import MINE_RATE
from app.logic.base.mine import Mine
from app.logic.base.post import Docked, Post, Services
from app.logic.base.sites import FRONTIER, ICARE
from app.logic.base.wallet import Wallet
from app.logic.ship.fuel import Tank
from app.logic.ship.heat import HullHeat


def test_a_mine_digs_slowly() -> None:
    mine = Mine(Random(1))
    stock: dict[str, float] = {}
    mine.update(stock, .9 / MINE_RATE)
    assert not stock
    mine.update(stock, .2 / MINE_RATE)
    assert sum(stock.values()) == 1.


def test_a_mine_digs_mostly_helium() -> None:
    stock: dict[str, float] = {}
    Mine(Random(2)).update(stock, 4000 / MINE_RATE)
    assert sum(stock.values()) == 4000.
    assert stock['helium3'] == pytest.approx(3 * stock['ice'], rel=.1)


def test_a_mine_has_no_limit() -> None:
    stock = {'helium3': 100000.}
    Mine(Random(3)).update(stock, 100 / MINE_RATE)
    assert sum(stock.values()) >= 100100.


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
