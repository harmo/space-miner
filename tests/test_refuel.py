import pytest

from app.logic.base.config import FREE_RESERVE, FUEL_PRICE, ICE_FUEL, TOW_BASE
from app.logic.base.refuel import Refuel, fill, refuel, tow, tow_price
from app.logic.base.wallet import Wallet
from app.logic.ship.fuel import Tank


def test_a_full_tank_takes_nothing() -> None:
    stock = {'ice': 10.}
    wallet = Wallet(500)
    assert refuel(0., wallet, stock) == Refuel(0., 0, 0.)
    assert stock == {'ice': 10.} and wallet.credits == 500


def test_ice_is_taken_first() -> None:
    stock = {'ice': 100., 'iron': 5.}
    wallet = Wallet(500)
    done = refuel(40., wallet, stock)
    assert done == Refuel(40. / ICE_FUEL, 0, 40.)
    assert stock == {'ice': 100. - 40. / ICE_FUEL, 'iron': 5.}
    assert wallet.credits == 500


def test_ice_of_the_cargo_goes_before_that_of_the_depot() -> None:
    cargo, depot = {'ice': 5.}, {'ice': 50.}
    done = refuel(40., Wallet(), cargo, depot)
    assert done.ice == 40. / ICE_FUEL
    assert cargo == {} and depot == {'ice': 50. - (40. / ICE_FUEL - 5.)}


def test_then_credits() -> None:
    stock = {'ice': 5.}
    wallet = Wallet(500)
    done = refuel(40., wallet, stock)
    rest = 40. - 5. * ICE_FUEL
    assert done == Refuel(5., round(rest * FUEL_PRICE), 40.)
    assert 'ice' not in stock
    assert wallet.credits == 500 - rest * FUEL_PRICE


def test_as_far_as_the_credits_go() -> None:
    wallet = Wallet(10)
    done = refuel(40., wallet)
    assert done.credits == 10 and wallet.credits == 0
    assert done.fuel == pytest.approx(10 / FUEL_PRICE)


def test_towing_costs_more_from_farther() -> None:
    assert tow_price(0.) == TOW_BASE
    assert tow_price(10000.) > tow_price(1000.) > TOW_BASE


def test_towing_takes_what_credits_there_are() -> None:
    wallet = Wallet(150)
    assert tow(100, wallet) == 100 and wallet.credits == 50
    assert tow(100, wallet) == 50 and wallet.credits == 0


def test_the_tank_is_filled_as_far_as_ice_and_credits_go() -> None:
    tank = Tank(100.)
    tank.burn(100.)
    stock = {'ice': 10.}
    wallet = Wallet(40)
    fill(tank, wallet, stock)
    assert tank.level == pytest.approx(10. * ICE_FUEL + 40 / FUEL_PRICE)
    assert stock == {} and wallet.credits == 0


def test_with_nothing_left_the_base_gives_a_reserve() -> None:
    tank = Tank(100.)
    tank.burn(100.)
    done = fill(tank, Wallet())
    assert done.fuel == 0. and tank.share == pytest.approx(FREE_RESERVE)
