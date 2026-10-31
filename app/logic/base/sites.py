""" The sites outposts are built on, and what each stage built there
offers the ships landing: fuel, a depot, then a market and missions. """

from dataclasses import dataclass, replace
from typing import Literal

from .config import PAD_WIDTH
from .post import Services

Form = Literal['ground', 'orbit']    # landed on, or docked to


@dataclass(frozen=True)
class Stage:
    """ A step of building an outpost """
    name: str                 # shown
    materials: tuple[tuple[str, int], ...]  # units to deliver, by mineral
    services: Services        # offered once built, those before included


@dataclass(frozen=True)
class Trade:
    """ What the market and the missions of an outpost pay """
    markup: float = 1.        # times what the Earth pays for ore
    dearer: tuple[tuple[str, float], ...] = ()  # times more for these
    bonus: float = 1.         # missions pay that much more
    clients: tuple[str, ...] = ()

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

    @property
    def gives_missions(self) -> bool:
        """ Whether it gives missions, once built far enough """
        return any(stage.services.missions for stage in self.stages)


FUEL = Services(fuel=True)
DEPOT = replace(FUEL, depot=True)
TRADING_POST = replace(DEPOT, market=True, missions=True)
REFINING = replace(DEPOT, market=True, refinery=True)
SHELTER = replace(FUEL, shelter=True)

# On the farthest planet from the sun, far from everything: ore is dearer
# there, ice most of all as fuel is lacking
FRONTIER = Site('Base Frontière', 'ground', (
    Stage('Fondations', (('rock', 120),), FUEL),
    Stage('Habitat', (('rock', 160), ('iron', 40)), DEPOT),
    Stage('Comptoir', (('rock', 200), ('iron', 60), ('copper', 30)),
          TRADING_POST),
), Trade(1.3, (('ice', 2.),), 1.25, (
    'Colonie Thulé', 'Relais Éclipse', 'Forge Boréale', 'Halte des Confins',
)))


# In the middle of the belt around the sun: a relay to mine, keep and
# crush ore there, without missions. Its pad is small, as it is.
CERES = Site('Comptoir de Cérès', 'ground', (
    Stage('Fondations', (('rock', 80),), FUEL),
    Stage('Entrepôt', (('rock', 120), ('iron', 30)), DEPOT),
    Stage('Raffinerie', (('rock', 150), ('iron', 40), ('copper', 20)),
          REFINING),
), pad_width=60.)

# Orbiting the first planet, close to the sun: a refuge to mine the ejecta
# of flares, paying well for them
_RING = replace(SHELTER, depot=True)
ICARE = Site('Station Icare', 'orbit', (
    Stage('Armature', (('rock', 100),), SHELTER),
    Stage('Anneau habitable', (('rock', 120), ('iron', 50)), _RING),
    Stage('Comptoir', (('rock', 150), ('iron', 60), ('copper', 30)),
          replace(_RING, market=True)),
), Trade(dearer=(('nebulite', 1.6), ('stellarium', 1.6),
                 ('antimatter', 1.6))), pad_width=40.)

# By the key they are saved under
SITES = {'frontier': FRONTIER, 'ceres': CERES, 'icare': ICARE}

# As told to the player
OFFERED = (
    ('fuel', 'le plein'), ('depot', 'un entrepôt'), ('market', 'un marché'),
    ('missions', 'des missions'), ('refinery', 'une raffinerie'),
    ('shelter', 'un abri contre la chaleur'),
)


def unlocked(stage: Stage, before: Services) -> list[str]:
    """ What building `stage` adds to what was offered `before` """
    return [
        told for name, told in OFFERED
        if getattr(stage.services, name) and not getattr(before, name)
    ]
