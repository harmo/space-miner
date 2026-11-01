""" The missions of a post: those offered on each level, coming back after
a while, and those accepted, paid into the wallet """

from dataclasses import dataclass, field
from random import Random

from ..mining.ore import Hold
from .config import MISSION_OFFERS, MISSION_REFILL, MISSIONS_ACTIVE
from .missions import (
    ANY_CLIENT,
    Clientele,
    Mission,
    make_mission,
    make_order,
    take,
)
from .reputation import Standing, tier
from .wallet import Wallet


@dataclass(frozen=True)
class Contracts:
    """ The missions of a board, as they are saved """
    offers: list[Mission] = field(default_factory=list)
    active: list[Mission] = field(default_factory=list)
    level: int = 1                      # of the missions offered
    # Seconds before the next offer, by level
    waits: dict[int, float] = field(default_factory=dict)


class Board:
    """ Missions offered on each level, and those accepted, paid into the
    wallet. An offer taken comes back after a while, level by level, and
    looking at another level changes nothing. Boards share the reputation
    they make: that of the Earth and those of the outposts. """

    def __init__(self, rng: Random, wallet: Wallet,
                 standing: Standing | None = None,
                 clientele: Clientele = ANY_CLIENT) -> None:
        self.rng = rng
        self.wallet = wallet
        self.standing = standing or Standing()
        self.clientele = clientele
        self.shelves: dict[int, list[Mission]] = {}  # offers, by level
        self.waits: dict[int, float] = {}   # before the next, by level
        self.active: list[Mission] = []
        self.level = 1                      # of the missions shown
        self.shelf(self.level)

    @property
    def validated(self) -> int:
        """ Missions, here and on the other boards """
        return self.standing.validated

    @validated.setter
    def validated(self, count: int) -> None:
        self.standing.validated = count

    @property
    def contracts(self) -> Contracts:
        return Contracts(
            [m for shelf in self.shelves.values() for m in shelf],
            list(self.active), self.level, dict(self.waits),
        )

    def resume(self, contracts: Contracts) -> None:
        """ As they were, its reputation known: levels never looked at get
        their offers when they are, as many as the reputation brings """
        self.level = max(1, min(contracts.level, self.tier))
        self.active[:] = contracts.active
        self.shelves.clear()
        for mission in contracts.offers:
            self.shelves.setdefault(mission.level, []).append(mission)
        self.waits = dict(contracts.waits)
        self.shelf(self.level)

    def make(self, level: int) -> Mission:
        clientele = self.clientele
        if clientele.orders:
            return make_order(self.rng, level, clientele)
        return make_mission(
            self.rng, level, clientele.clients, clientele.bonus,
        )

    def shelf(self, level: int) -> list[Mission]:
        """ Its offers, full the first time it is looked at """
        if level not in self.shelves:
            self.shelves[level] = [
                self.make(level) for _ in range(self.room)
            ]
        return self.shelves[level]

    @property
    def offers(self) -> list[Mission]:
        """ Those of the level shown """
        return self.shelf(self.level)

    @property
    def room(self) -> int:
        """ For offers on a level, at this reputation """
        return MISSION_OFFERS[self.tier - 1]

    def update(self, dt: float) -> None:
        """ Each level gets its offers back, one after the other """
        for level, shelf in self.shelves.items():
            if len(shelf) >= self.room:
                self.waits.pop(level, None)
                continue
            left = self.waits.get(level, MISSION_REFILL) - dt
            if left <= 0:
                shelf.append(self.make(level))
                left = MISSION_REFILL
            self.waits[level] = left

    @property
    def next_offer(self) -> float | None:
        """ Seconds before one comes on the level shown, None if it is
        full """
        if len(self.offers) >= self.room:
            return None
        return self.waits.get(self.level, MISSION_REFILL)

    @property
    def tier(self) -> int:
        return tier(self.validated)

    def choose_level(self, level: int) -> None:
        """ Up to the tier of the reputation """
        self.level = max(1, min(level, self.tier))

    @property
    def most(self) -> int:
        """ Missions under way at most, at this reputation """
        return MISSIONS_ACTIVE[self.tier - 1]

    @property
    def full(self) -> bool:
        return len(self.active) >= self.most

    def accept(self, mission: Mission) -> None:
        """ Another offer comes after a while """
        if self.full or mission not in self.offers:
            return
        self.offers.remove(mission)
        self.active.append(mission)

    def validate(self, mission: Mission, *holds: Hold) -> None:
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

    def abandon(self, mission: Mission) -> None:
        if mission in self.active:
            self.active.remove(mission)
