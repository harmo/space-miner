""" The ambience of space: drones of modular synthesizers, the game fading
from one to another at random, each a loop of LOOP seconds where every
slow sweep makes whole cycles """

import math
from dataclasses import dataclass
from random import Random

from .synth import (
    Samples,
    echo,
    envelope,
    length,
    looping,
    mix,
    noise,
    normalized,
    placed,
    resonant,
    reverb,
    saw,
    sine,
    times,
)

LOOP = 40.                    # seconds
PLUCK = 1.6                   # seconds a note of a sequence rings


@dataclass(frozen=True)
class Drone:
    """ A patch of the synthesizer. Notes are in semitones: those of the
    sequence above the octave of the root, those shimmering two octaves
    above it. """
    root: float               # Hz, of the bass
    interval: float           # of the second voice, times the root
    scale: tuple[int, ...]    # the notes the sequence picks from
    shimmer: tuple[int, ...]  # high notes swelling in and out
    sweep: tuple[float, float] = (180., 650.)  # Hz, cutoff of the bass
    ring: float = .2          # damping of the second voice, rings when low
    step: float = 2.5         # seconds between notes the sequence may play
    played: float = .45       # how often it does
    echo: float = .75         # seconds between echoes of its notes
    wash: float = .08         # share of wind of particles
    sub: float = 0.           # share of a sine an octave below the root

    def note(self, semitones: int, octaves: int) -> float:
        return float(self.root * 2 ** (octaves + semitones / 12))


# Around D, so that fading from one to another stays in tune
DRONES = (
    # D, pentatonic: the first one heard
    Drone(73.42, 1.5, (0, 2, 5, 7, 10, 12, 14, 17, 19), (0, 7, 14)),
    # A minor, low and slow
    Drone(55., 1.5, (0, 3, 7, 10, 12, 15, 19), (0, 7, 15),
          sweep=(150., 500.), step=3.3, played=.35, echo=1.1, sub=.3),
    # G lydian, bright
    Drone(98., 1.5, (0, 4, 6, 7, 11, 12, 16, 19), (0, 4, 11),
          sweep=(220., 900.), step=2., played=.5, echo=.5),
    # E phrygian, ominous, a fourth above
    Drone(82.41, 4 / 3, (0, 1, 5, 7, 8, 12, 13), (0, 1, 7),
          sweep=(160., 520.), ring=.12, step=4., played=.3, echo=1.2,
          wash=.14),
    # C pentatonic, airy, an octave above
    Drone(65.41, 2., (0, 2, 4, 7, 9, 12, 14, 16, 19), (0, 7, 16),
          sweep=(200., 800.), step=1.875, played=.4, echo=.625),
    # D minor, a minor third above
    Drone(73.42, 6 / 5, (0, 3, 5, 7, 10, 12, 15), (0, 3, 10),
          sweep=(170., 600.), step=3., played=.4, echo=.9, sub=.4),
    # F by whole tones, floating
    Drone(87.31, 1.5, (0, 2, 4, 6, 8, 10, 12, 14, 16), (0, 6, 10),
          sweep=(200., 700.), step=2.2, echo=.55, wash=.12),
    # A, deep and almost still
    Drone(55., 1.5, (0, 7, 12, 19), (0, 12, 19), sweep=(120., 400.),
          step=5., played=.15, wash=.1, sub=.5),
    # E dorian, pulsing
    Drone(82.41, 1.5, (0, 2, 3, 7, 9, 10, 12, 14), (0, 7, 14),
          sweep=(200., 900.), step=1.5, played=.55, echo=.375),
    # G suspended, very low, a fourth above
    Drone(49., 4 / 3, (0, 2, 5, 7, 12, 14, 17, 19), (0, 5, 14),
          sweep=(140., 480.), ring=.15, step=3.75, played=.35, echo=1.25,
          sub=.3),
)


def slow(n: int, cycles: int, low: float, high: float,
         phase: float = 0.) -> Samples:
    """ From `low` to `high` and back, `cycles` times over the loop, by
    equal ratios: as cutoffs and pitches are heard """
    step = 2 * math.pi * cycles / n
    return [
        low * (high / low) ** (.5 - .5 * math.cos(step * i + phase))
        for i in range(n)
    ]


def swell(n: int, cycles: int, phase: float = 0.) -> Samples:
    """ From silent to full and back, `cycles` times over the loop """
    step = 2 * math.pi * cycles / n
    return [(.5 - .5 * math.cos(step * i + phase)) ** 2 for i in range(n)]


def detuned(freq: float, n: int, apart: float) -> Samples:
    """ Two saws `apart` Hz from each other, beating slowly """
    return mix(
        (.5, saw(looping(freq, LOOP), n)),
        (.5, saw(looping(freq + apart, LOOP), n)),
    )


def bass(drone: Drone, n: int) -> Samples:
    """ The root, its filter opening and closing once over the loop """
    tone = resonant(detuned(drone.root, n, .1), slow(n, 1, *drone.sweep),
                    .35, loop=True)
    sub = sine(looping(drone.root / 2, LOOP), n)
    return normalized(mix((1., normalized(tone)), (drone.sub, sub)))


def second(drone: Drone, n: int) -> Samples:
    """ The second voice, ringing more, out of step with the bass """
    low, high = drone.sweep
    tone = resonant(
        detuned(drone.root * drone.interval, n, .2),
        slow(n, 2, low * 1.4, high * 2.2, math.pi / 3), drone.ring,
        loop=True,
    )
    return normalized(times(tone, [.4 + .6 * s for s in swell(n, 3)]))


def shimmer(drone: Drone, n: int) -> Samples:
    """ High notes swelling in and out, each at its own pace """
    return normalized(mix(*(
        (1., times(sine(looping(drone.note(note, 2), LOOP), n),
                   swell(n, cycles, phase)))
        for note, cycles, phase in zip(
            drone.shimmer, (4, 5, 3), (0., 2., 4.), strict=True,
        )
    )))


def pluck(freq: float) -> Samples:
    """ A note of the sequence: bright, closing fast """
    n = length(PLUCK)
    cutoff = [250. + 2250. * math.exp(-i / (.25 * n / PLUCK)) for i in
              range(n)]
    tone = resonant(saw(freq, n), cutoff, .3)
    return times(tone, envelope(n, .005, .5))


def sequence(drone: Drone, rng: Random, n: int) -> Samples:
    """ Now and then a note of the scale, echoing """
    notes = [
        placed(pluck(drone.note(rng.choice(drone.scale), 1)), n,
               step * drone.step)
        for step in range(round(LOOP / drone.step))
        if rng.random() < drone.played
    ]
    return normalized(echo(mix(*((1., note) for note in notes)),
                           drone.echo, .45, loop=True))


def wash(rng: Random, n: int) -> Samples:
    """ Wind of particles, sweeping slowly """
    return normalized(resonant(
        noise(rng, n), slow(n, 1, 400., 1600., math.pi), .5, loop=True,
        band=True,
    ))


def play(drone: Drone, rng: Random) -> Samples:
    n = length(LOOP)
    return reverb(mix(
        (1., bass(drone, n)), (.6, second(drone, n)),
        (.12, shimmer(drone, n)), (.35, sequence(drone, rng, n)),
        (drone.wash, wash(rng, n)),
    ), .35, loop=True)
