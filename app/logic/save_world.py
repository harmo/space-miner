""" What goes on in the solar system, as JSON: see save.py """

from dataclasses import asdict
from typing import Any, get_args

from .base.shuttles import Leg, Route, ShuttleState
from .mining.minerals import MINERALS
from .world.flares import Phase
from .world.layout import OrbiterPlan
from .world.state import CometState, EventsState, LostCanister


def route_of(data: Any) -> Route | None:
    if data is None:
        return None
    return Route(
        str(data['destination']),
        tuple(m for m in data['minerals'] if m in MINERALS),
    )


def shuttles_of(data: Any) -> dict[str, ShuttleState]:
    """ By post, older saves having none """
    return {
        str(post): ShuttleState(
            route_of(state['route']), leg_of(state['leg']),
            offset_of(state.get('offset')), float(state.get('heading', 0.)),
            {
                name: float(units)
                for name, units in dict(state['load']).items()
                if name in MINERALS
            },
        )
        for post, state in dict(data).items()
    }


def offset_of(data: Any) -> tuple[float, float] | None:
    """ None in older saves: it flies on from its dock """
    return None if data is None else (float(data[0]), float(data[1]))


def leg_of(data: Any) -> Leg:
    return next((leg for leg in get_args(Leg) if leg == data), 'waiting')


def shuttle_data(state: ShuttleState) -> dict[str, Any]:
    route = state.route
    return {
        'route': {
            'destination': route.destination,
            'minerals': list(route.minerals),
        } if route else None,
        'leg': state.leg, 'heading': state.heading, 'load': state.load,
        'offset': list(state.offset) if state.offset else None,
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
