""" Missions given on the Earth: bring back some rare ore, for money once
validated, from what was unloaded into the depot """

import math
from collections.abc import Sequence
from dataclasses import dataclass
from random import Random

from ..mining.minerals import MINED, MINERALS
from ..mining.ore import whole_units
from .config import (
    MISSION_AMOUNT,
    MISSION_BONUS,
    MISSION_GROWTH,
    MISSION_OFFERS,
    MISSION_RARER,
    MISSIONS_ACTIVE,
)
from .market import ore_value
from .reputation import Standing, tier
from .wallet import Wallet

CLIENTS = (
    'Fonderie Lunaire', "Coopérative d'Ishtar", 'Laboratoire Kepler',
    'Chantier orbital Vesta', 'Joaillerie Andromède', 'Centrale Hélios',
    'Institut Cassini', 'Ateliers de Titan', 'Comptoir Orion',
    'Consortium Halley',
)
# Common rock and ice are not worth a mission
WANTED = [name for name in MINED if name not in ('rock', 'ice')]


@dataclass(frozen=True)
class Mission:
    client: str
    wanted: dict[str, int]    # units of each mineral
    reward: int               # credits
    level: int = 1            # bigger and rarer orders, higher

    def missing(self, *holds: dict[str, float]) -> dict[str, int]:
        """ Units still lacking in the holds, the depot and the cargo, by
        mineral """
        lacking = {
            name: units - held(name, holds)
            for name, units in self.wanted.items()
        }
        return {name: units for name, units in lacking.items() if units > 0}

    def can_validate(self, *holds: dict[str, float]) -> bool:
        return not self.missing(*holds)


def held(name: str, holds: Sequence[dict[str, float]]) -> int:
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


def needs(missions: list[Mission],
          *holds: dict[str, float]) -> list[Need]:
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
    stock: dict[str, float]   # of its depot


def needs_at(desks: Sequence[Desk],
             cargo: dict[str, float]) -> list[Need]:
    """ Wanted at all the desks, against the cargo and the depots of those
    wanting each mineral, in the order of the minerals table """
    wanted: dict[str, int] = {}
    holds: dict[str, list[dict[str, float]]] = {}
    for desk in desks:
        for need in needs(desk.missions):
            name = need.mineral
            wanted[name] = wanted.get(name, 0) + need.wanted
            holds.setdefault(name, [cargo]).append(desk.stock)
    return [
        Need(name, held(name, holds[name]), wanted[name])
        for name in MINERALS if name in wanted
    ]


def make_mission(rng: Random, level: int = 1,
                 clients: Sequence[str] = CLIENTS,
                 bonus: float = 1.) -> Mission:
    """ One or two minerals, the rarer the fewer, picked as often as they
    are found. Missions of a higher level order more of them, and rare
    ones more often. Those of `clients` pay `bonus` times more. """
    flatten = 1 - MISSION_RARER * (level - 1)
    weights = [MINERALS[name].frequency ** flatten for name in WANTED]
    count = rng.choice((1, 1, 2))
    names: list[str] = []
    while len(names) < count:
        name = rng.choices(WANTED, weights)[0]
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
    value = sum(
        units * ore_value(MINERALS[name]) for name, units in wanted.items()
    )
    reward = max(10, round(value * MISSION_BONUS * bonus, -1))
    return Mission(rng.choice(clients), wanted, int(reward), level)


class Board:
    """ Missions offered, and those accepted, paid into the wallet. Boards
    share the reputation they make: that of the Earth and those of the
    outposts. """

    def __init__(self, rng: Random, wallet: Wallet,
                 standing: Standing | None = None,
                 clients: Sequence[str] = CLIENTS,
                 bonus: float = 1.) -> None:
        self.rng = rng
        self.wallet = wallet
        self.standing = standing or Standing()
        self.clients = clients
        self.bonus = bonus                  # missions pay that much more
        self.offers: list[Mission] = []
        self.active: list[Mission] = []
        self.level = 1                      # of the missions offered
        self.top_up()

    @property
    def validated(self) -> int:
        """ Missions, here and on the other boards """
        return self.standing.validated

    @validated.setter
    def validated(self, count: int) -> None:
        self.standing.validated = count

    def make(self) -> Mission:
        return make_mission(self.rng, self.level, self.clients, self.bonus)

    @property
    def tier(self) -> int:
        return tier(self.validated)

    def choose_level(self, level: int) -> None:
        """ Up to the tier of the reputation, with offers of that level """
        level = max(1, min(level, self.tier))
        if level != self.level:
            self.level = level
            self.offers.clear()
            self.top_up()

    @property
    def most(self) -> int:
        """ Missions under way at most, at this reputation """
        return MISSIONS_ACTIVE[self.tier - 1]

    @property
    def full(self) -> bool:
        return len(self.active) >= self.most

    def top_up(self) -> None:
        """ As many offers as the reputation brings """
        while len(self.offers) < MISSION_OFFERS[self.tier - 1]:
            self.offers.append(self.make())

    def accept(self, mission: Mission) -> None:
        """ A new offer takes its place """
        if self.full or mission not in self.offers:
            return
        index = self.offers.index(mission)
        self.offers[index] = self.make()
        self.active.append(mission)

    def validate(self, mission: Mission, *holds: dict[str, float]) -> None:
        """ Takes the ore from the holds, the first ones first, and pays """
        if mission not in self.active or not mission.can_validate(*holds):
            return
        for name, units in mission.wanted.items():
            take(name, units, holds)
        self.active.remove(mission)
        self.wallet.earn(mission.reward)
        reached = self.tier
        self.validated += 1
        # At the top, missions stay at the top
        if self.level == reached < self.tier:
            self.choose_level(self.tier)
        self.top_up()

    def abandon(self, mission: Mission) -> None:
        if mission in self.active:
            self.active.remove(mission)


def take(name: str, units: float, holds: Sequence[dict[str, float]]) -> None:
    """ From the first holds first, all the units being there """
    for hold in holds:
        taken = min(units, hold.get(name, 0.))
        if taken <= 0:
            continue
        hold[name] -= taken
        units -= taken
        if hold[name] <= 1e-6:
            del hold[name]
        if units <= 1e-6:
            return
