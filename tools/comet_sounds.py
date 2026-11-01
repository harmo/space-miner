""" The sound of a comet arriving: an omen, a hollow chord swelling, the
wind of its tail and bits of ice after it """

import math
from random import Random

from .sound_events import SoundEvent
from .sound_parts import chimes
from .synth import Samples, glide, mix, noise, normalized, resonant, times

CHORD = (220., 221.3, 329.6, 331.)      # Hz, in slightly beating pairs
RISE = 1.5                              # a fifth


def swell(n: int, peak: float) -> Samples:
    """ Rising to its top at `peak` of the way, then falling """
    top = round(n * peak)
    return [
        math.sin(math.pi / 2 * i / top) ** 2 if i < top
        else math.cos(math.pi / 2 * (i - top) / (n - top)) ** 2
        for i in range(n)
    ]


def sweep(
    n: int,
    low: float,
    high: float,
    end: float,
    peak: float
) -> Samples:
    """ Hz going from `low` up to `high` at `peak` of the way, then down
    to `end` """
    top = round(n * peak)
    return [
        low * (high / low) ** (i / top) if i < top
        else high * (end / high) ** ((i - top) / (n - top))
        for i in range(n)
    ]


def comet(rng: Random, n: int) -> Samples:
    """ The chord rising a fifth, the tail sweeping through the noise """
    chord = mix(*(
        (1., times(glide(freq, freq * RISE, n), swell(n, .6)))
        for freq in CHORD
    ))
    tail = resonant(
        noise(rng, n), sweep(n, 500., 1800., 600., .6), .25, band=True,
    )
    ice = times(chimes(rng, n, 3000., 6000., 16, .2), swell(n, .7))
    return mix(
        (1., normalized(chord)), (.5, times(normalized(tail), swell(n, .6))),
        (.22, ice),
    )


# Seconds long, and how it sounds
COMET_EVENTS = {'comet': SoundEvent(3., comet)}
