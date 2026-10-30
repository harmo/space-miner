""" Compose the sounds of the game, into assets/sounds/: the mining lasers,
one loop for each of their levels, the engines, one loop for each part
that can be fitted at the rear and one for the thrusters of the hulls,
asteroids breaking up when mined out, one sound for each mineral, and what
happens to the ship: picking canisters up, its hold full, its legs, its
landing and its crash, then the base: ore unloaded, trade, missions
validated and buttons clicked, and the solar system: swarms arriving and
the hum of space all around.

    uv run python -m tools.compose_sounds

ffmpeg encodes them, with libvorbis.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from random import Random

from .synth import (
    Samples,
    crackle,
    delayed,
    envelope,
    faded,
    glide,
    highpass,
    length,
    level,
    looping,
    lowpass,
    mix,
    noise,
    normalized,
    ring,
    save,
    saw,
    sine,
    throb,
    times,
)

SOUNDS_DIR = Path(__file__).parent.parent / 'assets' / 'sounds'
SEED = 5

# Loudness, in decibels: loops stay in the background, sounds of events
# rise a little above them at their loudest
LOOP_DB = -26.
EVENT_DB = -20.
CLICK_DB = -28.               # heard so often it must stay discreet
AMBIENT_DB = -32.             # always there, below everything
EVENT_WINDOW = .1             # seconds, their loudness is measured over
FADE = .4                     # seconds, at their end

LASER_LOOP = 2.               # seconds
ENGINE_LOOP = 3.
BREAKING = 1.5
UNLOAD_LOOP = 2.
AMBIENT_LOOP = 12.
SWARM_ALERT = 1.6


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

def rumble(rng: Random, n: int, cutoff: float) -> Samples:
    """ Roar of burning gas, deeper with a lower `cutoff` """
    gas = lowpass(noise(rng, n), cutoff, loop=True)
    return normalized(lowpass(gas, cutoff, loop=True))


def hiss(rng: Random, n: int, cutoff: float) -> Samples:
    """ Gas rushing out, above `cutoff` """
    return normalized(highpass(noise(rng, n), cutoff, loop=True))


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


# Asteroids breaking up, BREAKING seconds long: the rock bursting, and
# what it is made of ringing, tinkling, fizzing...

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
SHIP_EVENTS: dict[str, tuple[float, Callable[[Random, int], Samples]]] = {
    'pickup': (.6, pickup),
    'cargo_full': (.9, cargo_full),
    'explosion': (2.5, explosion),
    'gear_out': (.75, gear_out),
    'gear_in': (.75, gear_in),
    'touchdown': (.8, touchdown),
}


# At the base

def unloading(rng: Random) -> Samples:
    """ A loop of UNLOAD_LOOP seconds: a conveyor humming and ticking as
    ore rattles along it """
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
    ore = lowpass(crackle(rng, n, 40), 2500., loop=True)
    ore = normalized(highpass(ore, 300., loop=True))
    return mix((.6, motor), (.5, normalized(ticks)), (.4, ore))


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


# Seconds long, how they sound, and how loud
BASE_EVENTS: dict[
    str, tuple[float, Callable[[Random, int], Samples], float]
] = {
    'sale': (.7, sale, EVENT_DB),
    'purchase': (.7, purchase, EVENT_DB),
    'mission': (1.1, mission, EVENT_DB),
    'click': (.08, click, CLICK_DB),
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


def ambient(rng: Random) -> Samples:
    """ A loop of AMBIENT_LOOP seconds: a deep drone slowly breathing, a
    faint wind and shimmer """
    seconds = AMBIENT_LOOP
    n = length(seconds)

    def breathing(freq: float, rate: float, depth: float) -> Samples:
        return times(sine(looping(freq, seconds), n),
                     throb(looping(rate, seconds), n, depth))

    drone = mix(
        (1., breathing(55., 1 / 12, .5)), (.7, breathing(82.5, 1 / 6, .5)),
        (.5, breathing(110., 1 / 4, .6)),
    )
    shimmer = mix((1., breathing(1320., 1 / 6, .9)),
                  (.7, breathing(1980., 1 / 4, .9)))
    wind = normalized(lowpass(lowpass(noise(rng, n), 400., loop=True),
                              400., loop=True))
    wind = times(wind, throb(looping(1 / 6, seconds), n, .6))
    return mix(
        (1., normalized(drone)), (.3, wind), (.05, normalized(shimmer)),
    )


def event(rng: Random, seconds: float,
          compose: Callable[[Random, int], Samples],
          db: float = EVENT_DB) -> Samples:
    sound = faded(compose(rng, length(seconds)), min(FADE, seconds / 3))
    return level(sound, db, EVENT_WINDOW)


def main() -> None:
    rng = Random(SEED)
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    for number, beam in enumerate(BEAMS, start=1):
        save(SOUNDS_DIR / f'laser_{number}.ogg',
             level(laser(rng, beam), LOOP_DB))
    for name, compose in ENGINES.items():
        sound = compose(rng, length(ENGINE_LOOP))
        save(SOUNDS_DIR / f'engine_{name}.ogg', level(sound, LOOP_DB))
    for name, compose in BREAKS.items():
        save(SOUNDS_DIR / f'break_{name}.ogg',
             event(rng, BREAKING, compose))
    for name, (seconds, compose) in SHIP_EVENTS.items():
        save(SOUNDS_DIR / f'{name}.ogg', event(rng, seconds, compose))
    save(SOUNDS_DIR / 'unloading.ogg', level(unloading(rng), LOOP_DB))
    for name, (seconds, compose, db) in BASE_EVENTS.items():
        save(SOUNDS_DIR / f'{name}.ogg', event(rng, seconds, compose, db))
    save(SOUNDS_DIR / 'swarm.ogg', event(rng, SWARM_ALERT, swarm))
    save(SOUNDS_DIR / 'ambient.ogg', level(ambient(rng), AMBIENT_DB))


if __name__ == '__main__':
    main()
