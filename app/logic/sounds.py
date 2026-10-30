""" What the game sounds like: the sounds of the engine and the laser of
the ship, how loud its engine is, and what was heard from one frame to the
next. Sounds are named after their files in SOUNDS. """

from dataclasses import dataclass

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
    return name in ('ambient', 'unloading') or name.startswith(
        ('engine_', 'laser_')
    )


def toward(volume: float, target: float, dt: float) -> float:
    """ The volume of the engine, following its thrust """
    if target > volume:
        return min(target, volume + dt / ENGINE_RISE)
    return max(target, volume - dt / ENGINE_FALL)


@dataclass(frozen=True)
class Moment:
    """ What can be heard changing, on a frame """
    ship: int | None          # its entity, None while exploded
    parked: bool              # on the Earth
    legs_out: bool
    cargo_full: bool
    credits: int
    validated: int            # missions
    swarm: bool               # passing through the solar system


def heard(before: Moment, now: Moment) -> list[str]:
    """ Sounds of what happened between two frames. Legs and landings are
    only heard on the same ship, not on a new one. """
    sounds = []
    if before.ship is not None and now.ship is None:
        sounds.append('explosion')
    if before.ship is not None and now.ship == before.ship:
        if now.legs_out != before.legs_out:
            sounds.append('gear_out' if now.legs_out else 'gear_in')
        if now.parked and not before.parked:
            sounds.append('touchdown')
    if now.cargo_full and not before.cargo_full:
        sounds.append('cargo_full')
    if now.validated > before.validated:
        sounds.append('mission')
    elif now.credits > before.credits:
        sounds.append('sale')
    elif now.credits < before.credits:
        sounds.append('purchase')
    if now.swarm and not before.swarm:
        sounds.append('swarm')
    return sounds
