from random import Random

from app.logic.base.post import EVERYTHING, Docked, Post, Services
from app.logic.base.wallet import Wallet
from app.logic.ship.fuel import Tank


def empty_tank() -> Tank:
    tank = Tank(100.)
    tank.burn(100.)
    return tank


def test_a_post_fills_the_tank_of_a_ship_landed_there() -> None:
    post = Post('Terre', EVERYTHING, Random(1))
    tank = empty_tank()
    post.update(.1, Docked({}, tank), Wallet(1000))
    assert tank.share == 1.


def test_unless_it_offers_no_fuel() -> None:
    post = Post('Chantier', Services(depot=True), Random(2))
    tank = empty_tank()
    post.update(.1, Docked({}, tank), Wallet(1000))
    assert tank.empty


def test_it_takes_the_cargo_into_its_depot() -> None:
    post = Post('Terre', EVERYTHING, Random(3))
    ore = {'iron': 5.}
    post.depot.start(ore)
    post.update(10., Docked(ore, Tank(100.)), Wallet())
    assert ore == {} and post.depot.stock == {'iron': 5.}


def test_its_refinery_crushes_rock_with_no_ship_there() -> None:
    post = Post('Terre', EVERYTHING, Random(4))
    post.depot.stock['rock'] = 100.
    post.crusher.start(post.depot.stock)
    found = post.update(1., None, Wallet())
    assert found and post.depot.stock['rock'] < 100.


def test_none_without_a_refinery() -> None:
    post = Post('Chantier', Services(depot=True), Random(5))
    post.depot.stock['rock'] = 100.
    post.crusher.start(post.depot.stock)
    assert post.update(1., None, Wallet()) == []
    assert post.depot.stock['rock'] == 100.
