""" Sounds of what happens: to the ship, picking canisters up, its hold
full, its legs, its landing and its crash, at the base, its machines,
trade, missions validated and buttons clicked, and in the solar system,
swarms arriving """

from random import Random

from .sound_events import CLICK_DB, SoundEvent
from .sound_parts import bell, burst, chimes, debris, hiss, thump
from .synth import (
    Samples,
    crackle,
    delayed,
    envelope,
    glide,
    highpass,
    length,
    looping,
    lowpass,
    mix,
    noise,
    normalized,
    ring,
    saw,
    sine,
    throb,
    times,
)

UNLOAD_LOOP = 2.              # seconds, of the machines of the base
SWARM_ALERT = 1.6


# What happens to the ship

def pickup(rng: Random, n: int) -> Samples:
    """ A canister drawn in, clanking into the hold """
    pull = times(glide(300., 900., n), envelope(n, .15, .08))
    clank = delayed(bell(n, 620., (1., 2.76, 5.4), .08), .18)
    return mix(
        (.6, normalized(pull)), (.6, clank),
        (.5, delayed(thump(n, 140.), .18)),
    )


def beep(freq: float, n: int) -> Samples:
    return normalized(times(
        mix((1., sine(freq, n)), (.2, sine(freq * 2, n))),
        envelope(n, .005, .1),
    ))


def cargo_full(rng: Random, n: int) -> Samples:
    """ Two soft double beeps, high then low """
    return mix(*(
        (1., delayed(beep(freq, n), start))
        for freq, start in ((880., 0.), (660., .18), (880., .45),
                            (660., .63))
    ))


def explosion(rng: Random, n: int) -> Samples:
    """ A blast, the hull shattering, a long rumble """
    boom = times(glide(110., 25., n), envelope(n, .003, .5))
    return mix(
        (1., normalized(boom)), (.8, burst(rng, n, 400., .005, .7)),
        (.6, burst(rng, n, 3000., .002, .2)), (.4, debris(rng, n, 4000.)),
        (.25, chimes(rng, n, 800., 3000., 10, .15)),
        (.6, burst(rng, n, 150., .05, 1.2)),
    )


def servo(rng: Random, n: int, start: float, end: float) -> Samples:
    """ The legs moving for LEG_DEPLOY_TIME, whirring from `start` to
    `end` Hz, then locking in place """
    moving = length(.55)
    whir = mix(*(
        (1 / k, glide(start * k, end * k, moving)) for k in (1, 2, 3)
    ))
    grind = lowpass(noise(rng, moving), 1500.)
    whir = times(mix((1., normalized(whir)), (.2, normalized(grind))),
                 envelope(moving, .05, 1.))
    clunk = mix(
        (1., thump(n, 150.)), (.5, bell(n, 900., (1., 2.76), .05)),
    )
    return mix((.5, normalized(whir + [0.] * (n - moving))),
               (1., delayed(clunk, .55)))


def gear_out(rng: Random, n: int) -> Samples:
    """ Legs unfolding, the servos winding up """
    return servo(rng, n, 200., 320.)


def gear_in(rng: Random, n: int) -> Samples:
    """ Legs folding back, the servos winding down """
    return servo(rng, n, 320., 200.)


def touchdown(rng: Random, n: int) -> Samples:
    """ A soft thud, the legs sighing as they take the weight """
    sigh = normalized(times(hiss(rng, n, 2000.), envelope(n, .02, .2)))
    return mix(
        (1., thump(n, 70.)), (.4, sigh),
        (.3, bell(n, 300., (1., 2.76), .1)),
    )


# Seconds long, and how they sound
SHIP_EVENTS = {
    'pickup': SoundEvent(.6, pickup),
    'cargo_full': SoundEvent(.9, cargo_full),
    'explosion': SoundEvent(2.5, explosion),
    'gear_out': SoundEvent(.75, gear_out),
    'gear_in': SoundEvent(.75, gear_in),
    'touchdown': SoundEvent(.8, touchdown),
}


# At the base

def unloading(rng: Random) -> Samples:
    """ A loop of UNLOAD_LOOP seconds: a conveyor humming and ticking """
    seconds = UNLOAD_LOOP
    n = length(seconds)
    motor = saw(looping(90., seconds), n)
    motor = times(normalized(lowpass(motor, 500., loop=True)),
                  throb(looping(1.5, seconds), n, .2))
    tick = normalized(mix(
        (1., ring(1400., n, .006)),
        (.5, times(noise(rng, n), envelope(n, .0005, .004))),
    ))
    ticks = mix(*(
        (1., delayed(tick, k * seconds / 15)) for k in range(15)
    ))
    # Ore rattling along it, not heard any more: its random numbers stay
    # drawn, or the sounds composed after this one would change
    crackle(rng, n, 40)
    return mix((.6, motor), (.5, normalized(ticks)))


def crushing(rng: Random) -> Samples:
    """ A loop of UNLOAD_LOOP seconds: the refinery grinding rock, dull and
    steady, its jaws knocking twice a second """
    seconds = UNLOAD_LOOP
    n = length(seconds)
    motor = saw(looping(55., seconds), n)
    motor = normalized(lowpass(lowpass(motor, 300., loop=True), 300.,
                               loop=True))
    knocks = mix(*(
        (1., delayed(thump(n, 80.), k * seconds / 4)) for k in range(4)
    ))
    grind = lowpass(lowpass(noise(rng, n), 400., loop=True), 400.,
                    loop=True)
    grind = times(normalized(grind), throb(looping(4., seconds), n, .5))
    rocks = lowpass(crackle(rng, n, 30, decay=.012), 500., loop=True)
    return mix(
        (.6, motor), (.5, normalized(knocks)), (.6, grind),
        (.2, normalized(rocks)),
    )


def chirps(n: int, notes: tuple[float, ...], step: float,
           decay: float) -> Samples:
    """ Bright notes struck one after the other """
    return normalized(mix(*(
        (1., delayed(
            mix((1., ring(freq, n, decay)), (.3, ring(freq * 2, n, decay))),
            k * step,
        ))
        for k, freq in enumerate(notes)
    )))


def sale(rng: Random, n: int) -> Samples:
    """ Credits coming in: rising and sparkling """
    sweep = times(glide(800., 1600., n), envelope(n, .01, .05))
    return mix(
        (1., chirps(n, (1318.5, 1760., 2637.), .07, .15)),
        (.3, normalized(sweep)),
    )


def purchase(rng: Random, n: int) -> Samples:
    """ Credits going out, falling, and what was bought delivered """
    return mix(
        (1., chirps(n, (1760., 1318.5), .08, .15)),
        (.5, thump(n, 200.)),
    )


def mission(rng: Random, n: int) -> Samples:
    """ A rising arpeggio of bells, then a chord swelling, sparkling """
    arpeggio = chirps(n, (523.25, 659.25, 784., 1046.5), .06, .2)
    chord = normalized(mix(*(
        (1., ring(freq * (1 + .004 * k), n, .35, attack=.06))
        for freq in (523.25, 659.25, 784., 1046.5)
        for k in (-1, 1)
    )))
    return mix(
        (1., arpeggio), (.6, delayed(chord, .18)),
        (.25, delayed(chimes(rng, n, 3000., 6000., 8, .12), .2)),
    )


def click(rng: Random, n: int) -> Samples:
    """ A short tick """
    snap = times(noise(rng, n), envelope(n, .0005, .002))
    return mix((1., ring(1800., n, .01)), (.3, normalized(snap)))


# Seconds long, and how they sound
BASE_EVENTS = {
    'sale': SoundEvent(.7, sale),
    'purchase': SoundEvent(.7, purchase),
    'mission': SoundEvent(1.1, mission),
    'click': SoundEvent(.08, click, CLICK_DB),
}


# In the solar system

def swarm(rng: Random, n: int) -> Samples:
    """ Static on the radio, then a sonar ping echoing away """
    static = highpass(lowpass(noise(rng, n), 4000.), 1000.)
    static = normalized(times(static, envelope(n, .002, .05)))
    ping = normalized(mix((1., ring(1046.5, n, .25)),
                          (.5, ring(1568., n, .2))))
    echoes = mix(*(
        (weight, delayed(lowpass(ping, cutoff), start))
        for weight, cutoff, start in ((1., 20000., .08), (.4, 3000., .38),
                                      (.16, 1500., .68))
    ))
    return mix((.3, static), (1., normalized(echoes)))


SWARM = SoundEvent(SWARM_ALERT, swarm)
