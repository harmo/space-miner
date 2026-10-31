""" Sounds of the outposts: ore delivered to a site, a stage built, and a
ship docking to a station """

from random import Random

from .sound_events import SoundEvent
from .sound_parts import bell, debris, hiss, thump
from .synth import (
    Samples,
    crackle,
    delayed,
    envelope,
    glide,
    lowpass,
    mix,
    normalized,
    ring,
    sine,
    times,
)


def deliver(rng: Random, n: int) -> Samples:
    """ Ore pouring out: rocks rattling down a chute, a dull thud, the
    belt whirring """
    rocks = lowpass(crackle(rng, n, 50, decay=.006), 1800.)
    rocks = normalized(times(rocks, envelope(n, .05, .3)))
    whir = times(glide(120., 180., n), envelope(n, .02, .25))
    return mix(
        (1., rocks), (.7, delayed(thump(n, 70.), .15)),
        (.3, normalized(whir)),
    )


def built(rng: Random, n: int) -> Samples:
    """ Three blows of a hammer, then lights coming on: a rising arpeggio
    over a hum swelling """
    blows = mix(*(
        (1., delayed(mix((1., bell(n, 700., (1., 2.76, 5.4), .06)),
                         (.6, thump(n, 110.))), start))
        for start in (0., .16, .32)
    ))
    notes = mix(*(
        (1., delayed(ring(freq, n, .35), .55 + k * .09))
        for k, freq in enumerate((392., 493.88, 587.33, 783.99))
    ))
    hum = mix((1., sine(110., n)), (.5, sine(220., n)))
    hum = times(hum, delayed(envelope(n, .4, .8), .5))
    return mix(
        (.8, normalized(blows)), (.7, normalized(notes)),
        (.3, normalized(hum)),
    )


def dock(rng: Random, n: int) -> Samples:
    """ Clamps closing, the seals hissing, the latch clicking """
    clamps = mix((1., thump(n, 120.)), (.6, bell(n, 650., (1., 2.76), .05)),
                 (.3, debris(rng, n, 1500.)))
    seal = times(hiss(rng, n, 1500.), envelope(n, .02, .25))
    latch = ring(1500., n, .015)
    return mix(
        (1., normalized(clamps)), (.4, delayed(normalized(seal), .12)),
        (.6, delayed(latch, .55)),
    )


# Seconds long, and how they sound
OUTPOST_EVENTS = {
    'deliver': SoundEvent(1., deliver),
    'built': SoundEvent(1.8, built),
    'dock': SoundEvent(1.2, dock),
}
