import pytest

from app.logic.base.config import RESALE
from app.logic.base.shop import (
    Inventory,
    buy,
    buy_hull,
    can_buy,
    missing_materials,
    refit,
    rehull,
    resale_price,
    sell,
)
from app.logic.base.wallet import Wallet
from app.logic.ship.hulls import HULLS
from app.logic.ship.parts import PARTS
from app.logic.ship.shipyard import Design, ship_stats

QUANTUM = PARTS['quantum_laser']
MATERIALS = dict(QUANTUM.materials)


def test_every_part_has_a_price() -> None:
    assert all(part.price > 0 for part in PARTS.values())


def test_higher_tiers_cost_more() -> None:
    prices: dict[int, list[int]] = {}
    for part in PARTS.values():
        prices.setdefault(part.tier, []).append(part.price)
    tiers = sorted(prices)
    assert tiers == [1, 2, 3, 4, 5]
    for lower, higher in zip(tiers, tiers[1:], strict=False):
        assert max(prices[lower]) < min(prices[higher])


def test_buying_pays_credits_and_ore() -> None:
    wallet, inventory = Wallet(QUANTUM.price + 100), Inventory()
    stock = {name: units + 2. for name, units in MATERIALS.items()}
    stock['iron'] = 4.
    assert buy('quantum_laser', wallet, stock, inventory)
    assert wallet.credits == 100
    assert stock == {**{name: 2. for name in MATERIALS}, 'iron': 4.}
    assert inventory.count('quantum_laser') == 1


def test_buying_needs_the_credits() -> None:
    wallet, inventory = Wallet(100), Inventory()
    assert not buy('laser', wallet, {}, inventory)
    assert wallet.credits == 100
    assert inventory.count('laser') == 0


def test_buying_needs_the_ore() -> None:
    wallet, stock = Wallet(QUANTUM.price), {'crystal': 5.}
    assert missing_materials(QUANTUM, stock) == {
        name: units - (5 if name == 'crystal' else 0)
        for name, units in MATERIALS.items()
    }
    assert not can_buy(QUANTUM, wallet, stock)
    assert not buy('quantum_laser', wallet, stock, Inventory())
    assert stock == {'crystal': 5.} and wallet.credits == QUANTUM.price


def test_selling_back_only_gives_credits() -> None:
    wallet, inventory = Wallet(), Inventory()
    inventory.add('engine')
    assert sell('engine', wallet, inventory)
    assert wallet.credits == resale_price(PARTS['engine'])
    assert resale_price(PARTS['engine']) == pytest.approx(
        PARTS['engine'].price * RESALE, abs=1
    )
    assert not sell('engine', wallet, inventory)


def test_fitting_a_part_of_the_hangar() -> None:
    inventory = Inventory()
    inventory.add('laser')
    design = refit(Design(), 'nose', 'laser', inventory)
    assert design == Design(parts={'nose': 'laser'})
    assert inventory.count('laser') == 0


def test_the_part_taken_off_goes_back_to_the_hangar() -> None:
    inventory = Inventory()
    inventory.add('heavy_laser')
    design = refit(
        Design(parts={'nose': 'laser'}), 'nose', 'heavy_laser', inventory
    )
    assert design == Design(parts={'nose': 'heavy_laser'})
    assert inventory.spares == {'laser': 1}
    assert refit(design, 'nose', None, inventory) == Design()
    assert inventory.spares == {'laser': 1, 'heavy_laser': 1}


def test_only_parts_of_the_hangar_can_be_fitted() -> None:
    assert refit(Design(), 'nose', 'laser', Inventory()) is None


def test_both_sides_take_two_parts() -> None:
    inventory = Inventory()
    inventory.add('fins')
    design = refit(Design(), 'left', 'fins', inventory)
    assert design is not None
    assert refit(design, 'right', 'fins', inventory) is None


def test_cargo_must_hold_the_ore_on_board() -> None:
    inventory = Inventory()
    pods = Design(parts={'left': 'cargo_pod'})
    load = ship_stats(pods).capacity
    assert refit(pods, 'left', None, inventory, load) is None
    assert inventory.count('cargo_pod') == 0
    assert refit(pods, 'left', None, inventory, HULLS['scout'].capacity)


def test_buying_a_hull() -> None:
    hauler = HULLS['hauler']
    wallet, inventory = Wallet(hauler.price), Inventory()
    stock = {name: float(units) for name, units in hauler.materials}
    assert buy_hull('hauler', wallet, stock, inventory)
    assert inventory.hulls == {'scout', 'hauler'}
    assert wallet.credits == 0 and stock == {}
    wallet.earn(hauler.price)
    assert not buy_hull('hauler', wallet, stock, inventory)


def test_moving_onto_a_hull_of_the_hangar() -> None:
    inventory = Inventory()
    design = Design(parts={'nose': 'laser', 'left': 'fins'})
    assert rehull(design, 'cruiser', inventory) is None
    inventory.hulls.add('cruiser')
    cruiser = rehull(design, 'cruiser', inventory)
    assert cruiser is not None and cruiser.hull == 'cruiser'
    assert sorted(cruiser.parts.values()) == ['fins', 'laser']
    back = rehull(Design('cruiser', {
        'nose_left': 'laser', 'nose_right': 'heavy_laser',
    }), 'scout', inventory)
    assert back == Design(parts={'nose': 'laser'})
    assert inventory.spares == {'heavy_laser': 1}


def test_moving_needs_room_for_the_cargo() -> None:
    inventory = Inventory()
    inventory.hulls.add('hauler')
    load = HULLS['hauler'].capacity
    hauler = Design('hauler')
    assert rehull(hauler, 'scout', inventory, load) is None
