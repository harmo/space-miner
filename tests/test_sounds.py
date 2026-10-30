from dataclasses import replace
from pathlib import Path

import pytest

from app.logic.ambience import CALLS, DRONES
from app.logic.config import SOUNDS
from app.logic.mining.minerals import MINERALS
from app.logic.ship.lasers import BEST
from app.logic.ship.parts import PARTS
from app.logic.ship.shipyard import Design
from app.logic.sounds import (
    ENGINE_FALL,
    ENGINE_RISE,
    ENGINES,
    HULL_ENGINE,
    Moment,
    break_sound,
    engine_sound,
    heard,
    is_loop,
    laser_sound,
    toward,
)

ROOT = Path(__file__).parent.parent
FLYING = Moment(
    ship=7, parked=False, legs_out=False, cargo_full=False, credits=1000,
    validated=2, swarm=False,
)
EVENTS = (
    'explosion', 'gear_out', 'gear_in', 'touchdown', 'cargo_full',
    'mission', 'sale', 'purchase', 'swarm', 'pickup', 'click', 'unloading',
    'low_fuel', 'fuel_out', 'refuel', 'tow',
)


def test_every_sound_has_its_file() -> None:
    names = [
        HULL_ENGINE, *(f'engine_{part}' for part in ENGINES),
        *(laser_sound(level) for level in range(1, BEST + 1)),
        *(break_sound(name) for name in MINERALS), *EVENTS, *DRONES,
        *CALLS,
    ]
    for name in names:
        assert (ROOT / SOUNDS / f'{name}.ogg').is_file(), name


def test_loops_are_told_apart() -> None:
    loops = [
        'unloading', HULL_ENGINE, 'engine_fusion_engine', laser_sound(3),
        *DRONES,
    ]
    assert all(is_loop(name) for name in loops)
    assert not any(is_loop(name) for name in EVENTS if name not in loops)
    assert not any(is_loop(name) for name in CALLS)
    assert not is_loop(break_sound('gold'))


def test_engines_are_rear_parts() -> None:
    assert all(PARTS[part].kind == 'rear' for part in ENGINES)


def test_without_an_engine_the_hull_is_heard() -> None:
    assert engine_sound(Design()) == HULL_ENGINE
    assert engine_sound(Design(parts={'rear': 'rear_hold'})) == HULL_ENGINE


def test_an_engine_is_heard() -> None:
    design = Design(parts={'rear': 'ion_engine', 'left': 'ion_pod'})
    assert engine_sound(design) == 'engine_ion_engine'


def test_of_two_engines_the_most_expensive_is_heard() -> None:
    cruiser = Design('cruiser', {
        'rear_left': 'fusion_engine', 'rear_right': 'engine',
    })
    assert engine_sound(cruiser) == 'engine_fusion_engine'


def test_lasers_beyond_the_best_sound_as_it() -> None:
    assert laser_sound(1) == 'laser_1'
    assert laser_sound(BEST + 2) == f'laser_{BEST}'
    assert laser_sound(0) == 'laser_1'


def test_the_engine_rises_faster_than_it_falls() -> None:
    assert toward(0., 1., ENGINE_RISE / 2) == pytest.approx(.5)
    assert toward(1., 0., ENGINE_FALL / 2) == pytest.approx(.5)
    assert toward(.9, 1., 1.) == 1.
    assert toward(.1, 0., 1.) == 0.
    assert toward(.3, .3, 1.) == .3


def test_nothing_happening_is_not_heard() -> None:
    assert heard(FLYING, FLYING) == []


def test_crashing_is_heard() -> None:
    assert heard(FLYING, replace(FLYING, ship=None)) == ['explosion']


def test_landing_is_heard() -> None:
    legs = replace(FLYING, legs_out=True)
    assert heard(FLYING, legs) == ['gear_out']
    assert heard(legs, replace(legs, parked=True)) == ['touchdown']
    assert heard(replace(legs, parked=True), FLYING) == ['gear_in']


def test_a_new_ship_lands_silently() -> None:
    gone = replace(FLYING, ship=None)
    back = replace(FLYING, ship=8, parked=True, legs_out=True)
    assert heard(gone, back) == []


def test_a_full_cargo_is_heard_once() -> None:
    full = replace(FLYING, cargo_full=True)
    assert heard(FLYING, full) == ['cargo_full']
    assert heard(full, full) == []


def test_money_is_heard_coming_in_and_out() -> None:
    assert heard(FLYING, replace(FLYING, credits=1200)) == ['sale']
    assert heard(FLYING, replace(FLYING, credits=800)) == ['purchase']


def test_a_mission_validated_is_heard_rather_than_its_reward() -> None:
    validated = replace(FLYING, credits=1500, validated=3)
    assert heard(FLYING, validated) == ['mission']


def test_a_swarm_is_heard_arriving_not_leaving() -> None:
    swarm = replace(FLYING, swarm=True)
    assert heard(FLYING, swarm) == ['swarm']
    assert heard(swarm, FLYING) == []


def test_the_tank_running_low_then_dry_is_heard() -> None:
    low = replace(FLYING, gauge='critical', fuel=5.)
    assert heard(replace(FLYING, gauge='low'), low) == ['low_fuel']
    assert heard(low, low) == []
    dry = replace(FLYING, gauge='empty', stranded=True)
    assert heard(low, dry) == ['fuel_out']


def test_filling_the_tank_is_heard_rather_than_what_it_costs() -> None:
    parked = replace(FLYING, parked=True, legs_out=True, fuel=10.)
    filled = replace(parked, fuel=100., credits=800)
    assert heard(parked, filled) == ['refuel']


def test_towing_is_heard_rather_than_what_it_costs() -> None:
    dry = replace(FLYING, gauge='empty', stranded=True)
    back = replace(
        FLYING, ship=8, parked=True, legs_out=True, credits=700, fuel=0.,
    )
    assert heard(dry, back) == ['tow']
    filled = replace(back, fuel=100., gauge='full')
    assert heard(dry, filled) == ['tow', 'refuel']
