import pytest

from app.logic.base.config import FUEL_PRICE, ICE_FUEL, TOW_BASE
from app.logic.base.refuel import Refuel, refuel, tow, tow_price
from app.logic.base.wallet import Wallet


def test_a_full_tank_takes_nothing() -> None:
    stock = {'ice': 10.}
    wallet = Wallet(500)
    assert refuel(0., stock, wallet) == Refuel(0., 0, 0.)
    assert stock == {'ice': 10.} and wallet.credits == 500


def test_ice_is_taken_first() -> None:
    stock = {'ice': 100., 'iron': 5.}
    wallet = Wallet(500)
    done = refuel(40., stock, wallet)
    assert done == Refuel(40. / ICE_FUEL, 0, 40.)
    assert stock == {'ice': 100. - 40. / ICE_FUEL, 'iron': 5.}
    assert wallet.credits == 500


def test_then_credits() -> None:
    stock = {'ice': 5.}
    wallet = Wallet(500)
    done = refuel(40., stock, wallet)
    rest = 40. - 5. * ICE_FUEL
    assert done == Refuel(5., round(rest * FUEL_PRICE), 40.)
    assert 'ice' not in stock
    assert wallet.credits == 500 - rest * FUEL_PRICE


def test_as_far_as_the_credits_go() -> None:
    wallet = Wallet(10)
    done = refuel(40., {}, wallet)
    assert done.credits == 10 and wallet.credits == 0
    assert done.fuel == pytest.approx(10 / FUEL_PRICE)


def test_towing_costs_more_from_farther() -> None:
    assert tow_price(0.) == TOW_BASE
    assert tow_price(10000.) > tow_price(1000.) > TOW_BASE


def test_towing_takes_what_credits_there_are() -> None:
    wallet = Wallet(150)
    assert tow(100, wallet) == 100 and wallet.credits == 50
    assert tow(100, wallet) == 50 and wallet.credits == 0
