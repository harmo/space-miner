""" Compose the sounds of the game, into assets/sounds/, at their loudness:
those of the ship, see ship_sounds.py, of asteroids breaking up, see
mineral_sounds.py, of what happens, see event_sounds.py, of the fuel, see
fuel_sounds.py, of the sun, see sun_sounds.py, of the outposts, see
outpost_sounds.py, and the ambience of space, drones and radio calls, see
ambience.py.

    uv run python -m tools.compose_sounds [sounds] [fuel] [sun] [outposts]
        [ambience]

All of them without any, those named otherwise. Each group has random
numbers of its own, so that changing one leaves the others as they were.

ffmpeg encodes them, with libvorbis.
"""

import sys
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from random import Random

from .ambience import DRONES, calls, play
from .event_sounds import (
    BASE_EVENTS,
    SHIP_EVENTS,
    SWARM_ALERT,
    crushing,
    swarm,
    unloading,
)
from .fuel_sounds import FUEL_EVENTS
from .mineral_sounds import BREAKING, BREAKS
from .outpost_sounds import OUTPOST_EVENTS
from .ship_sounds import BEAMS, ENGINE_LOOP, ENGINES, laser
from .sun_sounds import SUN_EVENTS
from .synth import Samples, faded, length, level, save

SOUNDS_DIR = Path(__file__).parent.parent / 'assets' / 'sounds'
SEED = 5
AMBIENCE_SEED = 8
FUEL_SEED = 13
SUN_SEED = 21
OUTPOST_SEED = 34

# Loudness, in decibels, from the laser, which sounds right in the game:
# the other loops stay below it, as do sounds of events at their loudest
LASER_DB = -26.
LOOP_DB = -32.
EVENT_DB = -28.
FLARE_DB = -26.               # the sun blasting, above everything
BREAK_DB = -34.               # heard again and again while mining
CLICK_DB = -34.               # heard so often it must stay discreet
AMBIENT_DB = -30.             # always there, its volume set apart
RADIO_DB = -36.               # calls now and then over the ambience
EVENT_WINDOW = .1             # seconds, their loudness is measured over
FADE = .4                     # seconds, at their end


def event(rng: Random, seconds: float,
          compose: Callable[[Random, int], Samples],
          db: float = EVENT_DB) -> Samples:
    sound = faded(compose(rng, length(seconds)), min(FADE, seconds / 3))
    return level(sound, db, EVENT_WINDOW)


def main() -> None:
    rng = Random(SEED)
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    for number, beam in enumerate(BEAMS, start=1):
        save(SOUNDS_DIR / f'laser_{number}.ogg',
             level(laser(rng, beam), LASER_DB))
    for name, compose in ENGINES.items():
        sound = compose(rng, length(ENGINE_LOOP))
        save(SOUNDS_DIR / f'engine_{name}.ogg', level(sound, LOOP_DB))
    for name, compose in BREAKS.items():
        save(SOUNDS_DIR / f'break_{name}.ogg',
             event(rng, BREAKING, compose, BREAK_DB))
    for name, (seconds, compose) in SHIP_EVENTS.items():
        save(SOUNDS_DIR / f'{name}.ogg', event(rng, seconds, compose))
    save(SOUNDS_DIR / 'unloading.ogg', level(unloading(rng), LOOP_DB))
    for name, (seconds, compose) in BASE_EVENTS.items():
        db = CLICK_DB if name == 'click' else EVENT_DB
        save(SOUNDS_DIR / f'{name}.ogg', event(rng, seconds, compose, db))
    save(SOUNDS_DIR / 'swarm.ogg', event(rng, SWARM_ALERT, swarm))


def compose_drone(number: int) -> None:
    """ Each with random numbers of its own, apart from the other sounds """
    rng = Random(AMBIENCE_SEED + number - 1)
    sound = play(DRONES[number - 1], rng)
    save(SOUNDS_DIR / f'drone_{number}.ogg', level(sound, AMBIENT_DB))


def compose_fuel() -> None:
    """ With random numbers of their own, not to change the other sounds """
    rng = Random(FUEL_SEED)
    for name, (seconds, compose) in FUEL_EVENTS.items():
        save(SOUNDS_DIR / f'{name}.ogg', event(rng, seconds, compose))


def compose_sun() -> None:
    """ The sun, and the refinery, with random numbers of their own """
    rng = Random(SUN_SEED)
    for name, (seconds, compose) in SUN_EVENTS.items():
        db = FLARE_DB if name == 'flare' else EVENT_DB
        save(SOUNDS_DIR / f'{name}.ogg', event(rng, seconds, compose, db))
    save(SOUNDS_DIR / 'crushing.ogg', level(crushing(rng), LOOP_DB))


def compose_outposts() -> None:
    """ With random numbers of their own """
    rng = Random(OUTPOST_SEED)
    for name, (seconds, compose) in OUTPOST_EVENTS.items():
        save(SOUNDS_DIR / f'{name}.ogg', event(rng, seconds, compose))


def compose_ambience() -> None:
    """ The drones side by side, as they take long """
    with ProcessPoolExecutor() as pool:
        list(pool.map(compose_drone, range(1, len(DRONES) + 1)))
    rng = Random(AMBIENCE_SEED + len(DRONES))
    for name, call in calls(rng).items():
        save(SOUNDS_DIR / f'{name}.ogg',
             level(call, RADIO_DB, EVENT_WINDOW))


if __name__ == '__main__':
    # All of them, or the groups named
    wanted = sys.argv[1:] or ['sounds', 'fuel', 'sun', 'outposts', 'ambience']
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    if 'sounds' in wanted:
        main()
    if 'fuel' in wanted:
        compose_fuel()
    if 'sun' in wanted:
        compose_sun()
    if 'outposts' in wanted:
        compose_outposts()
    if 'ambience' in wanted:
        compose_ambience()
