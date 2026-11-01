""" Missions given at posts: bring back some rare ore, or for building
sites a lot of common ore, for money once validated, from what was
unloaded into the depot """

import math
from collections.abc import Sequence
from dataclasses import dataclass
from random import Random

from ..mining.minerals import MINED, MINERALS
from ..mining.ore import EPSILON, Hold, whole_units, withdraw
from .config import (
    MISSION_AMOUNT,
    MISSION_BONUS,
    MISSION_GROWTH,
    MISSION_PREMIUM,
    MISSION_RARER,
    ORDER_GROWTH,
)
from .market import ore_value

CLIENTS = (
    'Fonderie Lunaire', "Coopérative d'Ishtar", 'Laboratoire Kepler',
    'Chantier orbital Vesta', 'Joaillerie Andromède', 'Centrale Hélios',
    'Institut Cassini', 'Ateliers de Titan', 'Comptoir Orion',
    'Consortium Halley',
)
# Common rock and ice are not worth a mission
WANTED = [name for name in MINED if name not in ('rock', 'ice')]


@dataclass(frozen=True)
class Clientele:
    """ Those giving the missions of a board """
    clients: tuple[str, ...] = CLIENTS
    bonus: float = 1.         # they pay that much more
    # Building sites order these units of each, at the lowest level, rather
    # than rare ore
    orders: tuple[tuple[str, int], ...] = ()


ANY_CLIENT = Clientele()


@dataclass(frozen=True)
class Mission:
    client: str
    wanted: dict[str, int]    # units of each mineral
    reward: int               # credits
    level: int = 1            # bigger and rarer orders, higher

    def missing(self, *holds: Hold) -> dict[str, int]:
        """ Units still lacking in the holds, the depot and the cargo, by
        mineral """
        lacking = {
            name: units - held(name, holds)
            for name, units in self.wanted.items()
        }
        return {name: units for name, units in lacking.items() if units > 0}

    def can_validate(self, *holds: Hold) -> bool:
        return not self.missing(*holds)


def held(name: str, holds: Sequence[Hold]) -> int:
    """ Whole units of a mineral in all the holds """
    return whole_units(sum(hold.get(name, 0.) for hold in holds))


@dataclass(frozen=True)
class Need:
    """ Ore wanted by the missions under way, of one mineral """
    mineral: str
    held: int                 # in the cargo and the depot
    wanted: int

    @property
    def met(self) -> bool:
        return self.held >= self.wanted


def needs(
    missions: list[Mission],
    *holds: Hold
) -> list[Need]:
    """ Wanted by all the missions, against what the `holds` hold, in the
    order of the minerals table """
    wanted: dict[str, int] = {}
    for mission in missions:
        for name, units in mission.wanted.items():
            wanted[name] = wanted.get(name, 0) + units
    return [
        Need(name, held(name, holds), wanted[name])
        for name in MINERALS if name in wanted
    ]


@dataclass(frozen=True)
class Desk:
    """ Where missions are validated, the Earth or an outpost """
    missions: list[Mission]   # under way there
    stock: Hold   # of its depot


def needs_at(
    desks: Sequence[Desk],
    cargo: Hold
) -> list[Need]:
    """ Wanted at all the desks, against the cargo and the depots of those
    wanting each mineral, in the order of the minerals table """
    wanted: dict[str, int] = {}
    holds: dict[str, list[Hold]] = {}
    for desk in desks:
        for need in needs(desk.missions):
            name = need.mineral
            wanted[name] = wanted.get(name, 0) + need.wanted
            holds.setdefault(name, [cargo]).append(desk.stock)
    return [
        Need(name, held(name, holds[name]), wanted[name])
        for name in MINERALS if name in wanted
    ]


def paid(wanted: dict[str, int], bonus: float) -> int:
    """ For that ore, more than what it is worth """
    value = sum(
        units * ore_value(MINERALS[name]) for name, units in wanted.items()
    )
    return int(max(10, round(value * MISSION_BONUS * bonus, -1)))


def make_mission(
    rng: Random,
    level: int = 1,
    clients: Sequence[str] = CLIENTS,
    bonus: float = 1.
) -> Mission:
    """ One or two minerals, the rarer the fewer, picked as often as they
    are found, and what a laser of that level can mine. Missions of a
    higher level order more of them, rare ones more often, and pay more
    for each unit. Those of `clients` pay `bonus` times more. """
    flatten = 1 - MISSION_RARER * (level - 1)
    minerals = [name for name in WANTED if MINERALS[name].laser <= level]
    weights = [MINERALS[name].frequency ** flatten for name in minerals]
    count = rng.choice((1, 1, 2))
    names: list[str] = []
    while len(names) < count:
        name = rng.choices(minerals, weights)[0]
        if name not in names:
            names.append(name)
    share = 1. if count == 1 else .6
    share *= 1 + MISSION_GROWTH * (level - 1)
    wanted = {}
    for name in names:
        mineral = MINERALS[name]
        common = math.sqrt(mineral.frequency / MINERALS['iron'].frequency)
        amount = MISSION_AMOUNT * common * share * rng.uniform(.6, 1.4)
        wanted[name] = max(2, round(amount))
    premium = 1 + MISSION_PREMIUM * (level - 1)
    return Mission(
        rng.choice(clients), wanted, paid(wanted, bonus * premium), level,
    )


def make_order(rng: Random, level: int, clientele: Clientele) -> Mission:
    """ One or two common minerals by the shipload, as big as the level """
    count = rng.choice((1, 1, 2))
    share = 1. if count == 1 else .6
    share *= 1 + ORDER_GROWTH * (level - 1)
    wanted = {
        name: round(units * share * rng.uniform(.7, 1.3))
        for name, units in rng.sample(clientele.orders, count)
    }
    return Mission(
        rng.choice(clientele.clients), wanted,
        paid(wanted, clientele.bonus), level,
    )


def take(name: str, units: float, holds: Sequence[Hold]) -> None:
    """ From the first holds first, all the units being there """
    for hold in holds:
        taken = min(units, hold.get(name, 0.))
        if taken <= 0:
            continue
        withdraw(hold, name, taken)
        units -= taken
        if units <= EPSILON:
            return
