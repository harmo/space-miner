""" What the game sounds like: the sounds of the engine and the laser of
the ship, how loud its engine is, and what was heard from one frame to the
next. Sounds are named after their files in SOUNDS. """

from dataclasses import dataclass

from .ship.fuel import Gauge
from .ship.hulls import HULLS
from .ship.lasers import BEST
from .ship.parts import PARTS
from .ship.shipyard import Design

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
    return name == 'unloading' or name.startswith(
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


def heard(before: Moment, now: Moment) -> list[str]:
    """ Sounds of what happened between two frames. Legs, landings and the
    gauge are only heard on the same ship, not on a new one. Fuel put in
    the tank, or a ship towed back, is heard rather than the credits it
    cost. """
    sounds = []
    if before.ship is not None and now.ship is None:
        sounds.append('explosion')
    towed = before.stranded and now.ship not in (None, before.ship)
    if towed:
        sounds.append('tow')
    if before.ship is not None and now.ship == before.ship:
        if now.legs_out != before.legs_out:
            sounds.append('gear_out' if now.legs_out else 'gear_in')
        if now.parked and not before.parked:
            sounds.append('touchdown')
        if now.gauge != before.gauge:
            if now.gauge == 'critical' and before.gauge != 'empty':
                sounds.append('low_fuel')
            elif now.gauge == 'empty':
                sounds.append('fuel_out')
    refuelled = now.parked and now.fuel >= before.fuel + REFUEL_HEARD
    if refuelled:
        sounds.append('refuel')
    if now.cargo_full and not before.cargo_full:
        sounds.append('cargo_full')
    if now.validated > before.validated:
        sounds.append('mission')
    elif now.credits > before.credits:
        sounds.append('sale')
    elif now.credits < before.credits and not (towed or refuelled):
        sounds.append('purchase')
    if now.swarm and not before.swarm:
        sounds.append('swarm')
    return sounds
