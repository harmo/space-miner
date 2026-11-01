""" What a saved game keeps, as JSON: the progress of the player, and the
seed of its solar system. Parts or minerals unknown to this version of
the game are left out rather than failing. """

import json
from dataclasses import dataclass, field
from typing import Any

from .base.board import Contracts
from .base.missions import Mission
from .base.outposts import Progress
from .base.shuttles import ShuttleState
from .mining.minerals import MINERALS
from .mining.ore import Hold
from .save_world import (
    canister_data,
    canisters_of,
    events_data,
    events_of,
    shuttle_data,
    shuttles_of,
)
from .ship.hulls import HULLS
from .ship.parts import PARTS
from .ship.scanner import LOOKED_FOR
from .ship.shipyard import Design
from .world.state import EventsState, LostCanister

VERSION = 1


class SaveError(ValueError):
    """ Not a saved game of this version """


@dataclass(frozen=True)
class Landed:
    """ Where the ship was landed: it comes back there """
    place: str                          # 'earth', or the key of an outpost
    direction: float                    # from the center of its body


EARTH = 'earth'


@dataclass
class Save:
    seed: int  # of the solar system
    credits: int = 0
    design: Design = field(default_factory=Design)
    hulls: list[str] = field(default_factory=lambda: ['scout'])  # owned
    spares: dict[str, int] = field(default_factory=dict)
    stock: Hold = field(default_factory=dict)
    cargo: Hold = field(default_factory=dict)
    seen_tier: int = 1
    contracts: Contracts = field(default_factory=Contracts)
    # What the scanner looks for
    looked_for: list[str] = field(default_factory=lambda: list(LOOKED_FOR))
    fuel: float | None = None  # in the tank, None when full
    # By site, those not started left out
    outposts: dict[str, Progress] = field(default_factory=dict)
    # Saved in flight, the ship comes back on the Earth, its cargo lost
    landed: Landed | None = None
    concessions: list[str] = field(default_factory=list)  # granted
    followed: list[str] = field(default_factory=list)     # tracked in flight
    scan_missions: bool = False         # the scanner looks for what they lack
    # By post, those with a route or on their way
    shuttles: dict[str, ShuttleState] = field(default_factory=dict)
    canisters: list[LostCanister] = field(default_factory=list)
    # None in older saves: nothing going on
    events: EventsState | None = None


def ores(data: Any) -> Hold:
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


def contracts_of(data: Any) -> Contracts:
    """ Of a board, older saves having no level """
    return Contracts(
        missions(data.get('offers', [])), missions(data.get('active', [])),
        max(1, int(data.get('mission_level', 1))),
        {
            int(level): float(left)
            for level, left in dict(data.get('mission_waits', {})).items()
        },
        max(0, int(data.get('validated', 0))),
    )


def contracts_data(contracts: Contracts) -> dict[str, Any]:
    return {
        'offers': [mission_data(mission) for mission in contracts.offers],
        'active': [mission_data(mission) for mission in contracts.active],
        'mission_level': contracts.level,
        'mission_waits': {
            str(level): left for level, left in contracts.waits.items()
        },
        'validated': contracts.validated,
    }


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
            contracts_of(progress),
            bool(progress.get('followed', False)),
        )
        for site, progress in dict(data).items()
    }


def landed_of(data: Any) -> Landed | None:
    """ Older saves have none: on the Earth """
    if data is None:
        return None
    return Landed(str(data['place']), float(data['direction']))


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
        'seen_tier': save.seen_tier,
        **contracts_data(save.contracts),
        'looked_for': save.looked_for,
        'fuel': save.fuel,
        'outposts': {
            site: {
                'built': progress.built, 'delivered': progress.delivered,
                'stock': progress.stock, 'followed': progress.followed,
                **contracts_data(progress.contracts),
            }
            for site, progress in save.outposts.items()
        },
        'landed': {
            'place': save.landed.place,
            'direction': save.landed.direction,
        } if save.landed else None,
        'concessions': save.concessions,
        'followed': save.followed,
        'scan_missions': save.scan_missions,
        'shuttles': {
            post: shuttle_data(state) for post, state in save.shuttles.items()
        },
        'canisters': [canister_data(c) for c in save.canisters],
        'events': events_data(save.events) if save.events else None,
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
            seen_tier=max(1, int(data['seen_tier'])),
            contracts=contracts_of(data),
            looked_for=[
                name for name in MINERALS
                if name in data.get('looked_for', LOOKED_FOR)
            ],
            fuel=fuel_of(data.get('fuel')),
            outposts=outposts_of(data.get('outposts', {})),
            concessions=[str(key) for key in data.get('concessions', [])],
            followed=[str(key) for key in data.get('followed', [])],
            scan_missions=bool(data.get('scan_missions', False)),
            shuttles=shuttles_of(data.get('shuttles', {})),
            canisters=canisters_of(data.get('canisters', [])),
            events=events_of(data.get('events')),
            landed=landed_of(data.get('landed')),
        )
    except SaveError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise SaveError(str(error)) from error
