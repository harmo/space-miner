""" What many sounds are made of: rumbles and hisses of gas, the blow of a
burst, bits of rock flying apart, puffs of noise, struck metal and shards
tinkling. Each normalized, so that layers mix in the weights given. """

from random import Random

from .synth import (
    Samples,
    crackle,
    delayed,
    envelope,
    glide,
    highpass,
    lowpass,
    mix,
    noise,
    normalized,
    ring,
    times,
)


def rumble(rng: Random, n: int, cutoff: float) -> Samples:
    """ Roar of burning gas, deeper with a lower `cutoff` """
    gas = lowpass(noise(rng, n), cutoff, loop=True)
    return normalized(lowpass(gas, cutoff, loop=True))


def hiss(rng: Random, n: int, cutoff: float) -> Samples:
    """ Gas rushing out, above `cutoff` """
    return normalized(highpass(noise(rng, n), cutoff, loop=True))


def thump(n: int, freq: float) -> Samples:
    """ The blow of the burst, dropping an octave """
    return normalized(times(glide(freq, freq / 2, n),
                            envelope(n, .002, .1)))


def debris(rng: Random, n: int, cutoff: float) -> Samples:
    """ Bits of rock flying apart, brighter with a higher `cutoff` """
    bits = lowpass(crackle(rng, n, 60), cutoff)
    return normalized(times(bits, envelope(n, .001, .2)))


def burst(rng: Random, n: int, cutoff: float, attack: float,
          decay: float) -> Samples:
    """ A puff of noise """
    puff = lowpass(lowpass(noise(rng, n), cutoff), cutoff)
    return normalized(times(puff, envelope(n, attack, decay)))


def bell(n: int, base: float, partials: tuple[float, ...],
         decay: float) -> Samples:
    """ Struck metal: the higher partials fade faster """
    return normalized(mix(*(
        (1 / k, ring(base * ratio, n, decay / ratio ** .5))
        for k, ratio in enumerate(partials, start=1)
    )))


def chimes(rng: Random, n: int, low: float, high: float, count: int,
           decay: float) -> Samples:
    """ Shards tinkling, between `low` and `high` Hz, in the first half
    second """
    return normalized(mix(*(
        (rng.uniform(.3, 1), delayed(
            ring(rng.uniform(low, high), n, decay), rng.uniform(0, .5),
        ))
        for _ in range(count)
    )))

