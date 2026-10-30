""" What the game sounds like: the sounds of the engine and the laser of
the ship, how loud its engine is, and what was heard from one frame to the
next. Sounds are named after their files in SOUNDS. """

from dataclasses import dataclass

from .ship.fuel import Gauge
from .ship.heat import Warmth
from .ship.hulls import HULLS
from .ship.lasers import BEST
from .ship.parts import PARTS
from .ship.shipyard import Design
from .world.flares import Phase

# Rear parts with a sound of their own, the others sound as the hull
ENGINES = (
    'engine', 'vector_nozzle', 'afterburner', 'ion_engine', 'twin_engine',
    'solar_sail', 'fusion_engine',
)
HULL_ENGINE = 'engine_hull'
# Seconds for the engine to go from silent to full, and back
ENGINE_RISE = .15
ENGINE_FALL = .4
REFUEL_HEARD = .5             # units of fuel put in the tank at least


def engine_sound(design: Design) -> str:
    """ Of the most expensive engine at the rear, or of the hull """
    rear = [
        design.parts.get(slot_id)
        for slot_id, slot in HULLS[design.hull].slots.items()
        if slot.kind == 'rear'
    ]
    engines = [part for part in rear if part in ENGINES]
    if not engines:
        return HULL_ENGINE
    return 'engine_' + max(engines, key=lambda part: PARTS[part].price)


def laser_sound(level: int) -> str:
    """ Levels beyond the best one sound as it """
    return f'laser_{max(1, min(level, BEST))}'


def break_sound(mineral: str) -> str:
    """ An asteroid of `mineral` mined out """
    return f'break_{mineral}'


def is_loop(name: str) -> bool:
    """ Played over and over, rather than once """
    return name in ('unloading', 'crushing') or name.startswith(
        ('engine_', 'laser_', 'drone_')
    )


def toward(volume: float, target: float, dt: float) -> float:
    """ The volume of the engine, following its thrust """
    if target > volume:
        return min(target, volume + dt / ENGINE_RISE)
    return max(target, volume - dt / ENGINE_FALL)


@dataclass(frozen=True)
class Moment:
    """ What can be heard changing, on a frame """
    ship: int | None          # which one, None while exploded
    parked: bool              # on the Earth
    legs_out: bool
    cargo_full: bool
    credits: int
    validated: int            # missions
    swarm: bool               # passing through the solar system
    fuel: float = 0.          # in the tank
    gauge: Gauge = 'full'
    stranded: bool = False    # out of fuel away from the Earth
    warmth: Warmth = 'cool'   # of the hull
    flare: Phase = 'quiet'    # of the sun
    port: bool = False        # parked at the port of a station


def heard(before: Moment, now: Moment) -> list[str]:
    """ Sounds of what happened between two frames. Fuel put in the tank,
    or a ship towed back, is heard rather than the credits it cost. """
    towed = before.stranded and now.ship not in (None, before.ship)
    refuelled = now.parked and now.fuel >= before.fuel + REFUEL_HEARD
    return [
        *heard_of_ships(before, now, towed),
        *(['refuel'] if refuelled else []),
        *(['cargo_full'] if now.cargo_full and not before.cargo_full else []),
        *heard_of_money(before, now, towed or refuelled),
        *heard_of_space(before, now),
    ]


def heard_of_ships(before: Moment, now: Moment, towed: bool) -> list[str]:
    """ Lost, towed back, or what happened to the same one: legs, landings,
    fuel and heat are not heard on a new ship """
    sounds = []
    if before.ship is not None and now.ship is None:
        sounds.append('explosion')
    if towed:
        sounds.append('tow')
    if before.ship is not None and now.ship == before.ship:
        sounds += heard_of_ship(before, now)
    return sounds


def heard_of_ship(before: Moment, now: Moment) -> list[str]:
    sounds = []
    if now.legs_out != before.legs_out:
        sounds.append('gear_out' if now.legs_out else 'gear_in')
    if now.parked and not before.parked:
        sounds.append('dock' if now.port else 'touchdown')
    if now.gauge != before.gauge:
        if now.gauge == 'critical' and before.gauge != 'empty':
            sounds.append('low_fuel')
        elif now.gauge == 'empty':
            sounds.append('fuel_out')
    if now.warmth == 'overheating' != before.warmth:
        sounds.append('overheat')
    return sounds


def heard_of_money(before: Moment, now: Moment, paid_for: bool) -> list[str]:
    """ Missions validated rather than their reward, nothing for what is
    heard otherwise """
    if now.validated > before.validated:
        return ['mission']
    if now.credits > before.credits:
        return ['sale']
    if now.credits < before.credits and not paid_for:
        return ['purchase']
    return []


def heard_of_space(before: Moment, now: Moment) -> list[str]:
    """ Swarms arriving, flares told then blazing """
    sounds = []
    if now.swarm and not before.swarm:
        sounds.append('swarm')
    if now.flare != before.flare:
        if now.flare == 'warning':
            sounds.append('flare_warning')
        elif now.flare == 'blazing':
            sounds.append('flare')
    return sounds
