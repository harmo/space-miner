""" Sounds of the fuel: the tank running low, then dry, filled on the
Earth, and the distress beacon of a ship calling to be towed back """

from collections.abc import Callable
from random import Random

from .ambience import radio, static
from .synth import (
    RATE,
    Samples,
    crackle,
    delayed,
    envelope,
    glide,
    length,
    lowpass,
    mix,
    noise,
    normalized,
    resonant,
    ring,
    sine,
    times,
)


def bwoop(n: int, start: float, end: float) -> Samples:
    """ A short tone sliding down, hollow as a square wave """
    tone = mix((1., glide(start, end, n)), (.3, glide(start * 3, end * 3, n)))
    return normalized(times(tone, envelope(n, .01, .12)))


def low_fuel(rng: Random, n: int) -> Samples:
    """ Three insisting pulses, low and sliding down """
    return mix(*(
        (1., delayed(bwoop(n, 640., 520.), k * .25)) for k in range(3)
    ))


def fuel_out(rng: Random, n: int) -> Samples:
    """ The engine dying: winding down, coughing """
    whine = times(glide(420., 60., n), envelope(n, .01, .6))
    coughs = lowpass(crackle(rng, n, 10, decay=.02), 400.)
    coughs = times(coughs, envelope(n, .05, .5))
    return mix((1., normalized(whine)), (.6, normalized(coughs)))


def refuel(rng: Random, n: int) -> Samples:
    """ Fuel gurgling in, the tone rising as the tank fills, then the cap
    closing """
    filling = round(n * .8)
    flow = resonant(
        noise(rng, filling),
        [300. * 4 ** (i / filling) for i in range(filling)], .3, band=True,
    )
    bubbles = lowpass(noise(rng, filling), 12.)
    flow = times(normalized(flow), [.6 + 4 * abs(b) for b in bubbles])
    rise = glide(180., 420., filling)
    pour = times(mix((1., normalized(flow)), (.15, rise)),
                 envelope(filling, .1, 10.))
    cap = mix((1., ring(220., n, .06)), (.5, ring(900., n, .03)))
    return mix(
        (1., normalized(pour + [0.] * (n - filling))),
        (.7, delayed(normalized(cap), filling / RATE)),
    )


def tow(rng: Random, n: int) -> Samples:
    """ A distress beacon over the radio, its two tones taking turns """
    beacon: Samples = []
    beep = length(.15)
    for k in range(6):
        freq = 1000. if k % 2 == 0 else 750.
        beacon += times(sine(freq, beep), envelope(beep, .005, 10.))
        beacon += [0.] * length(.05)
    beacon += [0.] * (n - len(beacon))
    return mix((1., radio(beacon[:n])), (.08, static(rng, n)))


# Seconds long, and how they sound
FUEL_EVENTS: dict[str, tuple[float, Callable[[Random, int], Samples]]] = {
    'low_fuel': (1.1, low_fuel),
    'fuel_out': (1.6, fuel_out),
    'refuel': (1.4, refuel),
    'tow': (1.8, tow),
}
