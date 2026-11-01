from random import Random

from app.logic.base.board import Board
from app.logic.base.config import DEPOT_CAPACITY
from app.logic.base.missions import Mission
from app.logic.base.post import Docked, Post, Services, home_post
from app.logic.base.wallet import Wallet
from app.logic.ship.fuel import Tank
from app.logic.ship.heat import HullHeat


def empty_tank() -> Tank:
    tank = Tank(100.)
    tank.burn(100.)
    return tank


def test_a_post_fills_the_tank_of_a_ship_landed_there() -> None:
    post = home_post(Random(1))
    tank = empty_tank()
    post.update(.1, Docked({}, tank, HullHeat()), Wallet(1000))
    assert tank.share == 1.


def test_unless_it_offers_no_fuel() -> None:
    post = Post(Services(depot=True), Random(2))
    tank = empty_tank()
    post.update(.1, Docked({}, tank, HullHeat()), Wallet(1000))
    assert tank.empty


def test_it_takes_the_cargo_into_its_depot() -> None:
    post = home_post(Random(3))
    ore = {'iron': 5.}
    post.depot.start(ore)
    post.update(10., Docked(ore, Tank(100.), HullHeat()), Wallet())
    assert ore == {} and post.depot.stock == {'iron': 5.}


def test_its_refinery_crushes_rock_with_no_ship_there() -> None:
    post = home_post(Random(4))
    post.depot.stock['rock'] = 100.
    post.crusher.start(post.depot.stock)
    found = post.update(1., None, Wallet())
    assert found and post.depot.stock['rock'] < 100.


def test_none_without_a_refinery() -> None:
    post = Post(Services(depot=True), Random(5))
    post.depot.stock['rock'] = 100.
    post.crusher.start(post.depot.stock)
    assert post.update(1., None, Wallet()) == []
    assert post.depot.stock['rock'] == 100.


def test_a_shelter_cools_the_hull_down() -> None:
    post = Post(Services(shelter=True), Random(6))
    hull = HullHeat()
    hull.level = .9
    post.update(1., Docked({}, Tank(100.), hull), Wallet())
    assert hull.level < .9


def test_a_post_tells_a_cargo_can_unload_where_it_has_a_depot() -> None:
    assert home_post(Random(7)).status(
        {'iron': 5.}, None,
    ).can_unload
    assert not Post(Services(), Random(8)).status(
        {'iron': 5.}, None,
    ).can_unload


def test_a_mission_can_be_validated_from_the_depot_and_the_cargo() -> None:
    post = home_post(Random(9))
    board = Board(Random(10), Wallet())
    board.active.append(Mission('Institut Cassini', {'iron': 10}, 100))
    post.depot.stock['iron'] = 6.
    assert not post.status({}, board).to_validate
    assert post.status({'iron': 4.}, board).to_validate
    assert not post.status({'iron': 4.}, None).to_validate


def test_a_full_depot_tells_so_and_takes_no_cargo() -> None:
    post = Post(Services(depot=True), Random(11))
    post.depot.stock['iron'] = float(DEPOT_CAPACITY)
    status = post.status({'iron': 5.}, None)
    assert status.full and not status.can_unload
    status = post.status({'gold': 5.}, None)
    assert status.can_unload and not status.full
    assert not post.status({}, None).full
