""" Loops of the ship: its mining laser, one for each level, and its
engines, one for each part fitted at the rear and one for the thrusters
of the hulls """

from collections.abc import Callable
from dataclasses import dataclass
from random import Random

from .sound_parts import hiss, rumble
from .synth import (
    Samples,
    crackle,
    highpass,
    length,
    looping,
    lowpass,
    mix,
    noise,
    normalized,
    saw,
    sine,
    throb,
    times,
)

LASER_LOOP = 2.               # seconds
ENGINE_LOOP = 3.


@dataclass(frozen=True)
class Beam:
    """ Sound of a level of laser, deeper and brighter as it gets more
    powerful """
    hum: float                # Hz, the drone of its power
    voices: int               # slightly out of tune saws in the hum
    tone: float               # Hz, the hum is brighter above
    whine: tuple[float, ...]  # Hz, high pitched over the hum
    crackle: int              # clicks a second, of the rock it cuts
    pulse: float              # Hz, the beam throbs
    sub: float = 0.           # an octave below the hum, this much of it


# As the colors of their beams: red, orange, yellow, violet, cyan
BEAMS = (
    Beam(98., 2, 600., (1175.,), 12, 3.),
    Beam(110., 3, 900., (1320., 1980.), 18, 4., sub=.2),
    Beam(82.5, 3, 1300., (1650., 2475.), 24, 5., sub=.3),
    Beam(73.5, 5, 1600., (1470., 1478., 2205.), 30, 6., sub=.4),
    Beam(55., 5, 2200., (2200., 3300., 4400.), 36, 8., sub=.5),
)


def laser(rng: Random, beam: Beam) -> Samples:
    seconds = LASER_LOOP
    n = length(seconds)
    voices = [
        saw(looping(beam.hum * (1 + .006 * k), seconds), n)
        for k in range(-(beam.voices // 2), beam.voices - beam.voices // 2)
    ]
    hum = mix(*((1 / beam.voices, voice) for voice in voices))
    hum = lowpass(lowpass(hum, beam.tone, loop=True), beam.tone, loop=True)
    sub = sine(looping(beam.hum / 2, seconds), n)
    whine = mix(*(
        (1 / len(beam.whine), sine(looping(freq, seconds), n))
        for freq in beam.whine
    ))
    body = times(
        mix((1., hum), (beam.sub, sub), (.15, whine)),
        throb(looping(beam.pulse, seconds), n, .3),
    )
    rock = crackle(rng, n, round(beam.crackle * seconds))
    rock = lowpass(highpass(rock, 400., loop=True), 3000., loop=True)
    hiss = lowpass(noise(rng, n), 3000., loop=True)
    return mix((1., body), (.5, rock), (.08, hiss))


# Engines, as loops of ENGINE_LOOP seconds: the layers of each are
# normalized, so their weights are their shares of it

def tone(freq: float, n: int) -> Samples:
    return sine(looping(freq, ENGINE_LOOP), n)


def flutter(freq: float, n: int, depth: float) -> Samples:
    return throb(looping(freq, ENGINE_LOOP), n, depth)


def hull_thrusters(rng: Random, n: int) -> Samples:
    """ Small and soft """
    return times(
        mix((1., rumble(rng, n, 150.)), (.3, hiss(rng, n, 2000.))),
        flutter(5., n, .15),
    )


def engine(rng: Random, n: int) -> Samples:
    """ A plain rocket """
    return times(
        mix(
            (1., rumble(rng, n, 250.)), (.5, rumble(rng, n, 900.)),
            (.15, hiss(rng, n, 3000.)),
        ),
        flutter(11., n, .2),
    )


def vector_nozzle(rng: Random, n: int) -> Samples:
    """ Thinner, its roar sweeping from low to high as it turns """
    sweep = tone(.67, n)
    low = times(rumble(rng, n, 300.), [.6 + .4 * s for s in sweep])
    high = normalized(lowpass(hiss(rng, n, 600.), 2000., loop=True))
    high = times(high, [.6 - .4 * s for s in sweep])
    return times(mix((1., low), (.6, high)), flutter(13., n, .15))


def afterburner(rng: Random, n: int) -> Samples:
    """ Roaring, growling and popping """
    growl = saw(looping(45., ENGINE_LOOP), n)
    growl = normalized(lowpass(growl, 200., loop=True))
    pops = crackle(rng, n, round(14 * ENGINE_LOOP), decay=.006)
    pops = normalized(lowpass(pops, 1500., loop=True))
    return times(
        mix(
            (1., rumble(rng, n, 180.)), (.6, rumble(rng, n, 700.)),
            (.4, growl), (.5, pops),
        ),
        flutter(17., n, .25),
    )


def ion_engine(rng: Random, n: int) -> Samples:
    """ Electric: a humming chord, a whine and a faint hiss """
    hum = normalized(mix((1., tone(220., n)), (.5, tone(440., n)),
                         (.25, tone(660., n))))
    buzz = saw(looping(110., ENGINE_LOOP), n)
    buzz = normalized(lowpass(buzz, 1200., loop=True))
    whine = times(tone(3520., n), flutter(7., n, .5))
    return mix(
        (.5, hum), (.3, buzz), (.1, whine), (.25, hiss(rng, n, 4000.)),
        (.3, rumble(rng, n, 120.)),
    )


def twin_engine(rng: Random, n: int) -> Samples:
    """ Two rockets fluttering out of step, deeper together """
    return mix(
        (1., times(rumble(rng, n, 250.), flutter(11., n, .25))),
        (1., times(rumble(rng, n, 250.), flutter(13.33, n, .25))),
        (.5, rumble(rng, n, 900.)), (.5, rumble(rng, n, 80.)),
        (.15, hiss(rng, n, 3000.)),
    )


def solar_sail(rng: Random, n: int) -> Samples:
    """ Nothing burns: wind of the sun in the sail, shimmering """
    wind = normalized(lowpass(hiss(rng, n, 300.), 1200., loop=True))
    wind = times(wind, flutter(.33, n, .6))
    shimmer = mix(*(
        (1., times(tone(freq, n), flutter(rate, n, .8)))
        for freq, rate in ((1760., .67), (2217.5, 1.), (2637., 1.33))
    ))
    return mix((1., wind), (.15, normalized(shimmer)))


def fusion_engine(rng: Random, n: int) -> Samples:
    """ Deep and mighty, the whine of the fields holding the plasma """
    drone = mix(*(
        (1., saw(looping(82. * (1 + .006 * k), ENGINE_LOOP), n))
        for k in (-1, 0, 1)
    ))
    drone = normalized(lowpass(drone, 400., loop=True))
    whine = normalized(mix((1., tone(2960., n)), (1., tone(2967., n))))
    return times(
        mix(
            (.8, tone(41., n)), (.6, drone), (.7, rumble(rng, n, 400.)),
            (.08, whine),
        ),
        flutter(4., n, .3),
    )


# By part at the rear of the ship, 'hull' without any engine there
ENGINES: dict[str, Callable[[Random, int], Samples]] = {
    'hull': hull_thrusters,
    'engine': engine,
    'vector_nozzle': vector_nozzle,
    'afterburner': afterburner,
    'ion_engine': ion_engine,
    'twin_engine': twin_engine,
    'solar_sail': solar_sail,
    'fusion_engine': fusion_engine,
}

