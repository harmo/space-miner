""" Compose the sounds of the game, into assets/sounds/, at their loudness:
those of the ship, see ship_sounds.py, of asteroids breaking up, see
mineral_sounds.py, of what happens, see event_sounds.py, of the fuel, see
fuel_sounds.py, of the sun, see sun_sounds.py, of the outposts, see
outpost_sounds.py, and the ambience of space, drones and radio calls, see
ambience.py and radio_sounds.py.

    uv run python -m tools.compose_sounds [sounds] [fuel] [sun] [outposts]
        [ambience]

All of them without any, those named otherwise. Each group has random
numbers of its own, so that changing one leaves the others as they were.

ffmpeg encodes them, with libvorbis.
"""

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from random import Random

from .ambience import DRONES, play
from .event_sounds import (
    BASE_EVENTS,
    SHIP_EVENTS,
    SWARM,
    crushing,
    unloading,
)
from .fuel_sounds import FUEL_EVENTS
from .mineral_sounds import BREAKS
from .outpost_sounds import OUTPOST_EVENTS
from .radio_sounds import calls
from .ship_sounds import BEAMS, ENGINE_LOOP, ENGINES, laser
from .sound_events import (
    AMBIENT_DB,
    EVENT_WINDOW,
    LASER_DB,
    LOOP_DB,
    RADIO_DB,
    SoundEvent,
)
from .sun_sounds import SUN_EVENTS
from .synth import length, level, save

SOUNDS_DIR = Path(__file__).parent.parent / 'assets' / 'sounds'
SEED = 5
AMBIENCE_SEED = 8
FUEL_SEED = 13
SUN_SEED = 21
OUTPOST_SEED = 34


def save_events(
    rng: Random,
    events: dict[str, SoundEvent],
    prefix: str = ''
) -> None:
    for name, sound in events.items():
        save(SOUNDS_DIR / f'{prefix}{name}.ogg', sound.render(rng))


def main() -> None:
    rng = Random(SEED)
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    for number, beam in enumerate(BEAMS, start=1):
        save(SOUNDS_DIR / f'laser_{number}.ogg',
             level(laser(rng, beam), LASER_DB))
    for name, compose in ENGINES.items():
        sound = compose(rng, length(ENGINE_LOOP))
        save(SOUNDS_DIR / f'engine_{name}.ogg', level(sound, LOOP_DB))
    save_events(rng, BREAKS, 'break_')
    save_events(rng, SHIP_EVENTS)
    save(SOUNDS_DIR / 'unloading.ogg', level(unloading(rng), LOOP_DB))
    save_events(rng, BASE_EVENTS)
    save_events(rng, {'swarm': SWARM})


def compose_drone(number: int) -> None:
    """ Each with random numbers of its own, apart from the other sounds """
    rng = Random(AMBIENCE_SEED + number - 1)
    sound = play(DRONES[number - 1], rng)
    save(SOUNDS_DIR / f'drone_{number}.ogg', level(sound, AMBIENT_DB))


def compose_fuel() -> None:
    """ With random numbers of their own, not to change the other sounds """
    save_events(Random(FUEL_SEED), FUEL_EVENTS)


def compose_sun() -> None:
    """ The sun, and the refinery, with random numbers of their own """
    rng = Random(SUN_SEED)
    save_events(rng, SUN_EVENTS)
    save(SOUNDS_DIR / 'crushing.ogg', level(crushing(rng), LOOP_DB))


def compose_outposts() -> None:
    """ With random numbers of their own """
    save_events(Random(OUTPOST_SEED), OUTPOST_EVENTS)


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
