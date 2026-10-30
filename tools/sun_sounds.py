""" Sounds of the sun: the hull overheating, a flare told before, and the
flare blazing """

from collections.abc import Callable
from random import Random

from .synth import (
    Samples,
    crackle,
    envelope,
    glide,
    highpass,
    lowpass,
    mix,
    noise,
    normalized,
    throb,
    times,
)


def overheat(rng: Random, n: int) -> Samples:
    """ A fast pulsing alarm rising, over the sizzle of the hull """
    tone = mix((1., glide(820., 980., n)), (.3, glide(2460., 2940., n)))
    alarm = times(normalized(tone), throb(12., n, .9))
    sizzle = highpass(crackle(rng, n, 200, decay=.0008), 2500.)
    return times(
        mix((1., alarm), (.25, normalized(sizzle))), envelope(n, .02, .8),
    )


def whoop(n: int) -> Samples:
    """ Sliding up, as a dive alarm """
    tone = mix((1., glide(300., 600., n)), (.4, glide(600., 1200., n)))
    return normalized(times(tone, envelope(n, .05, .25)))


def flare_warning(rng: Random, n: int) -> Samples:
    """ Two whoops over a dull rumble """
    half = n // 2
    whoops = whoop(half) + whoop(n - half)
    rumble = normalized(lowpass(lowpass(noise(rng, n), 90.), 90.))
    return mix((1., whoops), (.5, times(rumble, envelope(n, .3, 1.5))))


def flare(rng: Random, n: int) -> Samples:
    """ The sun blasting: a deep roar, a rush of wind rising, fire """
    roar = lowpass(lowpass(noise(rng, n), 120.), 120.)
    roar = times(normalized(roar), envelope(n, .05, 1.2))
    boom = times(glide(70., 30., n), envelope(n, .01, .8))
    rush = lowpass(highpass(noise(rng, n), 400.), 2500.)
    rush = times(normalized(rush), envelope(n, .6, .8))
    fire = lowpass(crackle(rng, n, 150, decay=.004), 3000.)
    fire = times(normalized(fire), envelope(n, .3, 1.))
    return mix(
        (1., roar), (.8, normalized(boom)), (.5, rush), (.4, fire),
    )


# Seconds long, and how they sound
SUN_EVENTS: dict[str, tuple[float, Callable[[Random, int], Samples]]] = {
    'overheat': (1.2, overheat),
    'flare_warning': (2., flare_warning),
    'flare': (3., flare),
}
