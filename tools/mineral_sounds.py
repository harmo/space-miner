""" Asteroids breaking up when mined out, BREAKING seconds long, one sound
for each mineral: the rock bursting, and what it is made of ringing,
tinkling, fizzing... """

from collections.abc import Callable
from random import Random

from .sound_parts import bell, burst, chimes, debris, thump
from .synth import (
    Samples,
    crackle,
    envelope,
    glide,
    highpass,
    length,
    lowpass,
    mix,
    noise,
    normalized,
    ring,
    saw,
    times,
)

BREAKING = 1.5                # seconds


def rock(rng: Random, n: int) -> Samples:
    """ Crumbling """
    return mix(
        (1., thump(n, 80.)), (1., debris(rng, n, 1500.)),
        (.5, burst(rng, n, 300., .001, .15)),
    )


def ice(rng: Random, n: int) -> Samples:
    """ Shattering, glassy """
    return mix(
        (.6, thump(n, 120.)), (.6, debris(rng, n, 6000.)),
        (.7, chimes(rng, n, 2000., 6000., 14, .12)),
        (.3, burst(rng, n, 5000., .001, .1)),
    )


def iron(rng: Random, n: int) -> Samples:
    """ A heavy clang """
    return mix(
        (.8, thump(n, 70.)), (.6, debris(rng, n, 2500.)),
        (.7, bell(n, 190., (1., 2.76, 5.4, 8.93), .5)),
    )


def copper(rng: Random, n: int) -> Samples:
    """ Warmer than iron, ringing longer """
    return mix(
        (.7, thump(n, 80.)), (.5, debris(rng, n, 2500.)),
        (.8, bell(n, 262., (1., 2.32, 4.25, 6.63), .8)),
    )


def gold(rng: Random, n: int) -> Samples:
    """ A rich chime """
    return mix(
        (.5, thump(n, 90.)), (.3, debris(rng, n, 3000.)),
        (1., bell(n, 523.25, (1., 2., 2.4, 3., 4.07), 1.)),
    )


def crystal(rng: Random, n: int) -> Samples:
    """ A cascade of glass """
    return mix(
        (.5, thump(n, 100.)), (.4, debris(rng, n, 5000.)),
        (1., chimes(rng, n, 1500., 5000., 24, .25)),
    )


def uranium(rng: Random, n: int) -> Samples:
    """ Crackling like a Geiger counter, buzzing """
    geiger = crackle(rng, n, 120, decay=.0005)
    geiger = times(highpass(geiger, 1000.), envelope(n, .002, .4))
    buzz = lowpass(saw(60., n), 600.)
    buzz = times(buzz, envelope(n, .002, .3))
    return mix(
        (.7, thump(n, 70.)), (.6, debris(rng, n, 2000.)),
        (.8, normalized(geiger)), (.4, normalized(buzz)),
    )


def helium3(rng: Random, n: int) -> Samples:
    """ Gas escaping with a hiss, squealing up """
    gas = highpass(noise(rng, n), 1000.)
    gas = times(gas, envelope(n, .05, .3))
    squeal = times(glide(400., 1600., n), envelope(n, .01, .15))
    return mix(
        (.6, thump(n, 150.)), (.4, debris(rng, n, 3000.)),
        (1., normalized(gas)), (.2, normalized(squeal)),
    )


def ruby(rng: Random, n: int) -> Samples:
    """ A sharp ping, then shards """
    ping = mix((1., ring(1568., n, .4)), (.6, ring(2349., n, .3)))
    return mix(
        (.6, thump(n, 100.)), (.4, debris(rng, n, 4000.)),
        (.9, normalized(ping)),
        (.5, chimes(rng, n, 3000., 7000., 10, .08)),
    )


def nebulite(rng: Random, n: int) -> Samples:
    """ Ethereal: a chord swelling out of a breath, sparkling """
    pad = mix(*(
        (1., ring(freq * (1 + .004 * k), n, .5, attack=.15))
        for freq in (330., 415.3, 494., 659.)
        for k in (-1, 1)
    ))
    return mix(
        (.4, thump(n, 90.)), (.8, normalized(pad)),
        (.4, chimes(rng, n, 2500., 6000., 12, .3)),
        (.5, burst(rng, n, 2000., .15, .4)),
    )


def stellarium(rng: Random, n: int) -> Samples:
    """ A flare: bright, rising, burning """
    rise = times(glide(300., 1200., n), envelope(n, .02, .3))
    fire = lowpass(crackle(rng, n, 80), 3000.)
    fire = times(fire, envelope(n, .01, .5))
    return mix(
        (.8, thump(n, 60.)), (1., burst(rng, n, 4000., .005, .35)),
        (.3, normalized(rise)), (.6, normalized(fire)),
    )


def antimatter(rng: Random, n: int) -> Samples:
    """ Sucked in, then a deep boom """
    inward = length(.4)
    swell = lowpass(noise(rng, inward), 1500.)
    swell = [
        sample * (i / inward) ** 3 for i, sample in enumerate(swell)
    ]
    rest = n - inward
    boom = mix(
        (1., times(glide(120., 30., rest), envelope(rest, .002, .4))),
        (.3, times(glide(2000., 200., rest), envelope(rest, .002, .15))),
        (.5, burst(rng, rest, 600., .002, .3)),
    )
    return mix((.6, normalized(swell + [0.] * rest)),
               (1., normalized([0.] * inward + boom)))


# By mineral, as in the table of minerals
BREAKS: dict[str, Callable[[Random, int], Samples]] = {
    'rock': rock,
    'ice': ice,
    'iron': iron,
    'copper': copper,
    'gold': gold,
    'crystal': crystal,
    'uranium': uranium,
    'helium3': helium3,
    'ruby': ruby,
    'nebulite': nebulite,
    'stellarium': stellarium,
    'antimatter': antimatter,
}

