""" What a saved game keeps, as JSON: the progress of the player, and the
seed of its solar system. Parts or minerals unknown to this version of
the game are left out rather than failing. """

import json
from dataclasses import dataclass, field
from typing import Any

from .base.missions import Mission
from .mining.minerals import MINERALS
from .ship.hulls import HULLS
from .ship.parts import PARTS
from .ship.scanner import LOOKED_FOR
from .ship.shipyard import Design

VERSION = 1


class SaveError(ValueError):
    """ Not a saved game of this version """


@dataclass(frozen=True)
class Progress:
    """ Of an outpost being built """
    built: int = 0                      # stages
    delivered: dict[str, int] = field(default_factory=dict)
    stock: dict[str, float] = field(default_factory=dict)  # of its depot

    @property
    def started(self) -> bool:
        return bool(self.built or self.delivered or self.stock)


@dataclass
class Save:
    seed: int                           # of the solar system
    credits: int = 0
    design: Design = field(default_factory=Design)
    hulls: list[str] = field(default_factory=lambda: ['scout'])  # owned
    spares: dict[str, int] = field(default_factory=dict)
    stock: dict[str, float] = field(default_factory=dict)
    cargo: dict[str, float] = field(default_factory=dict)
    validated: int = 0
    seen_tier: int = 1
    offers: list[Mission] = field(default_factory=list)
    active: list[Mission] = field(default_factory=list)
    mission_level: int = 1              # of the missions offered
    # What the scanner looks for
    looked_for: list[str] = field(default_factory=lambda: list(LOOKED_FOR))
    fuel: float | None = None           # in the tank, None when full
    # By site, those not started left out
    outposts: dict[str, Progress] = field(default_factory=dict)


def ores(data: Any) -> dict[str, float]:
    return {
        name: float(units) for name, units in dict(data).items()
        if name in MINERALS and float(units) > 0
    }


def mission_data(mission: Mission) -> dict[str, Any]:
    return {
        'client': mission.client, 'wanted': mission.wanted,
        'reward': mission.reward, 'level': mission.level,
    }


def mission_of(data: Any) -> Mission | None:
    wanted = {
        name: int(units) for name, units in dict(data['wanted']).items()
    }
    if not wanted or any(name not in MINERALS for name in wanted):
        return None
    return Mission(
        str(data['client']), wanted, int(data['reward']),
        max(1, int(data.get('level', 1))),
    )


def missions(data: Any) -> list[Mission]:
    found = (mission_of(item) for item in data)
    return [mission for mission in found if mission is not None]


def design_of(data: Any) -> Design:
    hull = str(data['hull'])
    if hull not in HULLS:
        return Design()
    slots = HULLS[hull].slots
    return Design(hull, {
        slot: part for slot, part in dict(data['parts']).items()
        if slot in slots and part in PARTS
        and PARTS[part].kind == slots[slot].kind
    })


def hulls_of(data: Any, design: Design) -> list[str]:
    """ Known ones, the first one and that of the ship always included.
    Older saves have none. """
    owned = {'scout', design.hull, *(str(hull) for hull in data)}
    return [hull for hull in HULLS if hull in owned]


def fuel_of(data: Any) -> float | None:
    """ Older saves have none: a full tank """
    return None if data is None else max(0., float(data))


def outposts_of(data: Any) -> dict[str, Progress]:
    """ Older saves have none started """
    return {
        str(site): Progress(
            max(0, int(progress['built'])),
            {
                name: int(units)
                for name, units in dict(progress['delivered']).items()
                if name in MINERALS and int(units) > 0
            },
            ores(progress.get('stock', {})),
        )
        for site, progress in dict(data).items()
    }


def dump(save: Save) -> str:
    return json.dumps({
        'version': VERSION,
        'seed': save.seed,
        'credits': save.credits,
        'design': {'hull': save.design.hull, 'parts': save.design.parts},
        'hulls': save.hulls,
        'spares': save.spares,
        'stock': save.stock,
        'cargo': save.cargo,
        'validated': save.validated,
        'seen_tier': save.seen_tier,
        'offers': [mission_data(mission) for mission in save.offers],
        'active': [mission_data(mission) for mission in save.active],
        'looked_for': save.looked_for,
        'mission_level': save.mission_level,
        'fuel': save.fuel,
        'outposts': {
            site: {
                'built': progress.built, 'delivered': progress.delivered,
                'stock': progress.stock,
            }
            for site, progress in save.outposts.items()
        },
    }, ensure_ascii=False, indent=1, sort_keys=True)


def load(text: str) -> Save:
    try:
        data = json.loads(text)
        if data.get('version') != VERSION:
            raise SaveError(f'version {data.get("version")!r}')
        design = design_of(data['design'])
        return Save(
            seed=int(data['seed']),
            credits=max(0, int(data['credits'])),
            design=design,
            hulls=hulls_of(data.get('hulls', []), design),
            spares={
                part: int(count)
                for part, count in dict(data['spares']).items()
                if part in PARTS and int(count) > 0
            },
            stock=ores(data['stock']),
            cargo=ores(data['cargo']),
            validated=max(0, int(data['validated'])),
            seen_tier=max(1, int(data['seen_tier'])),
            offers=missions(data['offers']),
            active=missions(data['active']),
            mission_level=max(1, int(data.get('mission_level', 1))),
            looked_for=[
                name for name in MINERALS
                if name in data.get('looked_for', LOOKED_FOR)
            ],
            fuel=fuel_of(data.get('fuel')),
            outposts=outposts_of(data.get('outposts', {})),
        )
    except SaveError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise SaveError(str(error)) from error
