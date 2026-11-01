""" What a saved game keeps, as JSON: the progress of the player, and the
seed of its solar system. Parts or minerals unknown to this version of
the game are left out rather than failing. """

import json
from dataclasses import asdict, dataclass, field
from typing import Any, get_args

from .base.missions import Contracts, Mission
from .base.outposts import Progress
from .mining.minerals import MINERALS
from .mining.ore import Hold
from .ship.hulls import HULLS
from .ship.parts import PARTS
from .ship.scanner import LOOKED_FOR
from .ship.shipyard import Design
from .world.flares import Phase
from .world.layout import OrbiterPlan
from .world.state import CometState, EventsState, LostCanister

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
    seed: int                           # of the solar system
    credits: int = 0
    design: Design = field(default_factory=Design)
    hulls: list[str] = field(default_factory=lambda: ['scout'])  # owned
    spares: dict[str, int] = field(default_factory=dict)
    stock: Hold = field(default_factory=dict)
    cargo: Hold = field(default_factory=dict)
    validated: int = 0
    seen_tier: int = 1
    contracts: Contracts = field(default_factory=Contracts)
    # What the scanner looks for
    looked_for: list[str] = field(default_factory=lambda: list(LOOKED_FOR))
    fuel: float | None = None           # in the tank, None when full
    # By site, those not started left out
    outposts: dict[str, Progress] = field(default_factory=dict)
    # Saved in flight, the ship comes back on the Earth, its cargo lost
    landed: Landed | None = None
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
    )


def contracts_data(contracts: Contracts) -> dict[str, Any]:
    return {
        'offers': [mission_data(mission) for mission in contracts.offers],
        'active': [mission_data(mission) for mission in contracts.active],
        'mission_level': contracts.level,
        'mission_waits': {
            str(level): left for level, left in contracts.waits.items()
        },
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
        )
        for site, progress in dict(data).items()
    }


def canisters_of(data: Any) -> list[LostCanister]:
    """ Those of minerals known to this version """
    return [
        LostCanister(
            str(item['mineral']), float(item['amount']),
            float(item['altitude']), int(item['around']),
            (float(item['x']), float(item['y'])),
        )
        for item in data if item['mineral'] in MINERALS
    ]


def canister_data(canister: LostCanister) -> dict[str, Any]:
    return {
        'mineral': canister.mineral, 'amount': canister.amount,
        'altitude': canister.altitude, 'around': canister.around,
        'x': canister.offset[0], 'y': canister.offset[1],
    }


def plans_of(data: Any) -> list[OrbiterPlan]:
    """ Of asteroids of minerals known to this version """
    return [
        OrbiterPlan(**item) for item in data if item['mineral'] in MINERALS
    ]


def comet_of(data: Any) -> CometState | None:
    if data is None:
        return None
    return CometState(
        float(data['anomaly']), float(data['tilt']), int(data['sense']),
        int(data['shed']), plans_of(data['debris']),
    )


def phase_of(data: Any) -> Phase:
    """ Quiet if unknown to this version """
    return next((phase for phase in get_args(Phase) if phase == data), 'quiet')


def events_of(data: Any) -> EventsState | None:
    """ Older saves have none """
    if data is None:
        return None
    return EventsState(
        phase_of(data['flare_phase']), float(data['flare_left']),
        plans_of(data['ejecta']), float(data['swarm_waiting']),
        float(data['swarm_left']), plans_of(data['swarm']),
        float(data['comet_waiting']), comet_of(data['comet']),
    )


def events_data(events: EventsState) -> dict[str, Any]:
    comet = events.comet
    return {
        'flare_phase': events.flare_phase, 'flare_left': events.flare_left,
        'ejecta': [asdict(plan) for plan in events.ejecta],
        'swarm_waiting': events.swarm_waiting,
        'swarm_left': events.swarm_left,
        'swarm': [asdict(plan) for plan in events.swarm],
        'comet_waiting': events.comet_waiting,
        'comet': {
            'anomaly': comet.anomaly, 'tilt': comet.tilt,
            'sense': comet.sense, 'shed': comet.shed,
            'debris': [asdict(plan) for plan in comet.debris],
        } if comet else None,
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
        'validated': save.validated,
        'seen_tier': save.seen_tier,
        **contracts_data(save.contracts),
        'looked_for': save.looked_for,
        'fuel': save.fuel,
        'outposts': {
            site: {
                'built': progress.built, 'delivered': progress.delivered,
                'stock': progress.stock,
                **contracts_data(progress.contracts),
            }
            for site, progress in save.outposts.items()
        },
        'landed': {
            'place': save.landed.place,
            'direction': save.landed.direction,
        } if save.landed else None,
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
            validated=max(0, int(data['validated'])),
            seen_tier=max(1, int(data['seen_tier'])),
            contracts=contracts_of(data),
            looked_for=[
                name for name in MINERALS
                if name in data.get('looked_for', LOOKED_FOR)
            ],
            fuel=fuel_of(data.get('fuel')),
            outposts=outposts_of(data.get('outposts', {})),
            canisters=canisters_of(data.get('canisters', [])),
            events=events_of(data.get('events')),
            landed=landed_of(data.get('landed')),
        )
    except SaveError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise SaveError(str(error)) from error
