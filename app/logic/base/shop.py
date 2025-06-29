""" Hulls and parts of the ship: bought with credits and ore from the
depot, kept in the hangar. Parts are fitted on the ship and taken off for
free, and sold back for less than they cost. The ship is moved onto any
hull of the hangar, with its parts. """

from typing import Protocol

from ..mining.ore import whole_units
from ..ship.hulls import HULLS
from ..ship.parts import PARTS, Part
from ..ship.shipyard import Design, fitted, ship_stats, transfer
from .config import RESALE
from .wallet import Wallet


class Buyable(Protocol):
    """ A hull or a part """

    @property
    def price(self) -> int: ...

    @property
    def materials(self) -> tuple[tuple[str, int], ...]: ...


class Inventory:
    """ Parts in the hangar, not on the ship, and the hulls owned """

    def __init__(self) -> None:
        self.spares: dict[str, int] = {}
        self.hulls = {'scout'}              # the first one is given

    def count(self, part_id: str) -> int:
        return self.spares.get(part_id, 0)

    def add(self, part_id: str) -> None:
        self.spares[part_id] = self.count(part_id) + 1

    def take(self, part_id: str) -> None:
        if not self.count(part_id):
            raise ValueError(f'no {part_id} in the hangar')
        self.spares[part_id] -= 1
        if not self.spares[part_id]:
            del self.spares[part_id]


def missing_materials(item: Buyable,
                      stock: dict[str, float]) -> dict[str, int]:
    """ Ore lacking in the depot to build it, by mineral """
    lacking = {
        name: units - whole_units(stock.get(name, 0.))
        for name, units in item.materials
    }
    return {name: units for name, units in lacking.items() if units > 0}


def can_buy(item: Buyable, wallet: Wallet,
            stock: dict[str, float]) -> bool:
    return wallet.can_pay(item.price) and not missing_materials(item, stock)


def pay(item: Buyable, wallet: Wallet, stock: dict[str, float]) -> bool:
    """ With credits and ore, when there are enough """
    if not can_buy(item, wallet, stock):
        return False
    wallet.pay(item.price)
    for name, units in item.materials:
        stock[name] -= units
        if stock[name] <= 1e-6:
            del stock[name]
    return True


def buy(part_id: str, wallet: Wallet, stock: dict[str, float],
        inventory: Inventory) -> bool:
    """ Into the hangar """
    if not pay(PARTS[part_id], wallet, stock):
        return False
    inventory.add(part_id)
    return True


def buy_hull(hull_id: str, wallet: Wallet, stock: dict[str, float],
             inventory: Inventory) -> bool:
    if hull_id in inventory.hulls or not pay(HULLS[hull_id], wallet, stock):
        return False
    inventory.hulls.add(hull_id)
    return True


def rehull(design: Design, hull_id: str, inventory: Inventory,
           load: float = 0.) -> Design | None:
    """ The ship moved onto another hull of the hangar, with the parts that
    fit, the others going to the hangar. None when the hull isn't owned,
    or when the cargo couldn't hold the `load` anymore. """
    if hull_id not in inventory.hulls:
        return None
    moved, left = transfer(design, hull_id)
    if ship_stats(moved).capacity < load:
        return None
    for part_id in left:
        inventory.add(part_id)
    return moved


def resale_price(part: Part) -> int:
    """ Credits only: the ore it took is lost """
    return round(part.price * RESALE)


def sell(part_id: str, wallet: Wallet, inventory: Inventory) -> bool:
    """ A part in the hangar, not one on the ship """
    if not inventory.count(part_id):
        return False
    inventory.take(part_id)
    wallet.earn(resale_price(PARTS[part_id]))
    return True


def refit(design: Design, slot_id: str, part_id: str | None,
          inventory: Inventory, load: float = 0.) -> Design | None:
    """ The design with a part of the hangar on the slot, or nothing, the
    part there going back to the hangar. None when the part isn't in the
    hangar, or when the cargo couldn't hold the `load` anymore. """
    current = design.parts.get(slot_id)
    if part_id == current:
        return design
    if part_id is not None and not inventory.count(part_id):
        return None
    candidate = fitted(design, slot_id, part_id)
    if ship_stats(candidate).capacity < load:
        return None
    if part_id is not None:
        inventory.take(part_id)
    if current is not None:
        inventory.add(current)
    return candidate
