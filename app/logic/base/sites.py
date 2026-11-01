""" The sites outposts are built on, and what each stage built there
offers the ships landing: fuel, a depot, then a market and missions. """

from dataclasses import dataclass, replace
from typing import Literal

from .config import (
    ARES_YIELDS,
    CERES_CRUSH_RATE,
    CERES_CRUSH_YIELDS,
    FRONTIER_MINE_RATE,
    PAD_WIDTH,
)
from .crushing import PLAIN_REFINERY, Refinery
from .mine import PLAIN_VEIN, Vein
from .missions import ANY_CLIENT, Clientele, Mission
from .permits import Permit
from .post import Services

Form = Literal['ground', 'orbit']    # landed on, or docked to


@dataclass(frozen=True)
class Stage:
    """ A step of building an outpost """
    name: str                 # shown
    materials: tuple[tuple[str, int], ...]  # units to deliver, by mineral
    services: Services        # offered once built, those before included
    permit: Permit | None = None        # needed to build it


@dataclass(frozen=True)
class Trade:
    """ What the market and the missions of an outpost pay """
    markup: float = 1.        # times what the Earth pays for ore
    dearer: tuple[tuple[str, float], ...] = ()  # times more for these
    clientele: Clientele = ANY_CLIENT  # of its missions, if it gives any

    def factor(self, mineral: str) -> float:
        """ Times what the Earth pays for `mineral` """
        return self.markup * dict(self.dearer).get(mineral, 1.)


@dataclass(frozen=True)
class Site:
    """ Where an outpost is built, and how """
    name: str                 # shown
    form: Form
    stages: tuple[Stage, ...]
    trade: Trade = Trade()
    pad_width: float = PAD_WIDTH  # pixels, where ships land
    refinery: Refinery = PLAIN_REFINERY  # once it has one
    vein: Vein = PLAIN_VEIN             # of its mine, once it has one

    @property
    def gives_missions(self) -> bool:
        """ Whether it gives missions, once built far enough """
        return any(stage.services.missions for stage in self.stages)


def docked(services: Services) -> Stage:
    """ The dock of shuttles, on top of what an outpost offers """
    return Stage(
        'Quai des navettes', DOCK_MATERIALS, replace(services, dock=True),
    )


def concession(
    key: str,
    tier: int,
    name: str,
    wanted: dict[str, int],
    reward: int
) -> Permit:
    return Permit(key, tier, Mission(name, wanted, reward, tier))


ARES_MINE = concession(
    'ares_mine', 2, 'Mine de Mars',
    {'iron': 120, 'copper': 60}, 2000,
)
FRONTIER_TRADE = concession(
    'frontier_trade', 2, 'Licence Neptune',
    {'iron': 200, 'copper': 100}, 3000,
)
CERES_REFINERY = concession(
    'ceres_refinery', 3, 'Raffinage Cérès',
    {'iron': 300, 'copper': 150, 'gold': 30}, 6000,
)
ICARE_TRADE = concession(
    'icare_trade', 3, 'Licence Icare',
    {'gold': 60, 'crystal': 40}, 6000,
)
FRONTIER_MINE = concession(
    'frontier_mine', 4, 'Mine de Neptune',
    {'iron': 400, 'copper': 200, 'crystal': 40}, 12000,
)
# As shown on the Earth, the easiest first
PERMITS = (
    ARES_MINE, FRONTIER_TRADE, CERES_REFINERY, ICARE_TRADE, FRONTIER_MINE,
)

FUEL = Services(fuel=True)
DEPOT = replace(FUEL, depot=True)
TRADING_POST = replace(DEPOT, market=True, missions=True)
MINING = replace(TRADING_POST, mine=True)
DIGGING = replace(DEPOT, mine=True)
DOCK_MATERIALS = (('rock', 120), ('iron', 60), ('copper', 30))
REFINING = replace(DEPOT, market=True, missions=True, refinery=True)
SHELTER = replace(FUEL, shelter=True)

# On the farthest planet from the sun, far from everything: ore is dearer
# there, ice most of all as fuel is lacking, and a mine digs helium-3 and
# ice out of it, on its own
FRONTIER = Site('Base Frontière', 'ground', (
    Stage('Fondations', (('rock', 120),), FUEL),
    Stage('Habitat', (('rock', 160), ('iron', 40)), DEPOT),
    Stage('Comptoir', (('rock', 200), ('iron', 60), ('copper', 30)),
          TRADING_POST, FRONTIER_TRADE),
    Stage('Mine', (('rock', 260), ('iron', 100), ('copper', 60),
                   ('crystal', 15)), MINING, FRONTIER_MINE),
    docked(MINING),
), Trade(1.3, (('ice', 2.),), Clientele((
    'Colonie Thulé', 'Relais Éclipse', 'Forge Boréale', 'Halte des Confins',
), 1.25)), vein=Vein(rate=FRONTIER_MINE_RATE))


# In the middle of the belt around the sun: a relay to mine, keep and
# crush ore there, for the building sites of the belt ordering it by the
# shipload. Its pad is small, as it is, and its refinery the best there
# is, among so much rock.
CERES = Site('Comptoir de Cérès', 'ground', (
    Stage('Fondations', (('rock', 80),), FUEL),
    Stage('Entrepôt', (('rock', 120), ('iron', 30)), DEPOT),
    Stage('Raffinerie', (('rock', 150), ('iron', 40), ('copper', 20)),
          REFINING, CERES_REFINERY),
    docked(REFINING),
), Trade(clientele=Clientele((
    'Chantier Vesta', 'Mines de Pallas', "Cité d'Hygie", 'Forges de Junon',
), 1., (('rock', 120), ('regolith', 60), ('iron', 50), ('copper', 40)))),
    pad_width=60., refinery=Refinery(
    CERES_CRUSH_RATE, CERES_CRUSH_YIELDS,
    'trois fois plus vite, et plus riche en or, cristal, rubis',
))

# Orbiting the first planet, close to the sun: a refuge to mine the ejecta
# of flares, paying well for them
_RING = replace(SHELTER, depot=True)
ICARE = Site('Station Icare', 'orbit', (
    Stage('Armature', (('rock', 100),), SHELTER),
    Stage('Anneau habitable', (('rock', 120), ('iron', 50)), _RING),
    Stage('Comptoir', (('rock', 150), ('iron', 60), ('copper', 30)),
          replace(_RING, market=True), ICARE_TRADE),
    docked(replace(_RING, market=True)),
), Trade(dearer=(('nebulite', 1.6), ('stellarium', 1.6),
                 ('antimatter', 1.6))), pad_width=40.)

# On Mars, next to the Earth: a mine of metals and dust, for the ore to be
# carried away as there is nothing to trade there
ARES = Site('Base Ares', 'ground', (
    Stage('Fondations', (('rock', 60),), FUEL),
    Stage('Entrepôt', (('rock', 90), ('iron', 20)), DEPOT),
    Stage('Mine', (('rock', 150), ('iron', 50), ('copper', 25)), DIGGING,
          ARES_MINE),
    docked(DIGGING),
), vein=Vein(ARES_YIELDS))

# By the key they are saved under
SITES = {
    'frontier': FRONTIER, 'ceres': CERES, 'icare': ICARE, 'ares': ARES,
}

# As told to the player
OFFERED = (
    ('fuel', 'le plein'), ('depot', 'un entrepôt'), ('market', 'un marché'),
    ('missions', 'des missions'), ('refinery', 'une raffinerie'),
    ('shelter', 'un abri contre la chaleur'), ('mine', 'une mine'),
    ('dock', 'un quai de navettes'),
)


# As shown on the map
SHOWN = (
    ('fuel', 'Plein'), ('depot', 'Entrepôt'), ('market', 'Marché'),
    ('missions', 'Missions'), ('refinery', 'Raffinerie'), ('shelter', 'Abri'),
    ('mine', 'Mine'), ('dock', 'Quai'),
)


def offered(services: Services) -> str:
    """ What a post offers, in a few words """
    return ' · '.join(
        word for name, word in SHOWN if getattr(services, name)
    ) or 'Chantier'


def unlocked(stage: Stage, before: Services) -> list[str]:
    """ What building `stage` adds to what was offered `before` """
    return [
        told for name, told in OFFERED
        if getattr(stage.services, name) and not getattr(before, name)
    ]
