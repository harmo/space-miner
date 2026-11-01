""" Radio calls the game plays now and then over the ambience:
transmissions framed by the Quindar tones of the Apollo missions, and
telemetry beeping """

from random import Random

from .synth import (
    Samples,
    crackle,
    envelope,
    faded,
    highpass,
    length,
    lowpass,
    mix,
    noise,
    normalized,
    resonant,
    sine,
    times,
)

# Quindar tones, opening and closing a transmission, as on Apollo
QUINDAR_OPEN = 2525.
QUINDAR_CLOSE = 2475.
QUINDAR = .25                 # seconds
RADIO_BAND = (300., 3000.)    # Hz, what a radio lets through
# Talk, as the formants of distant voices, in Hz
FORMANTS = (500., 700., 900., 1200., 1600., 2200.)


def radio(samples: Samples) -> Samples:
    """ As heard through a radio """
    low, high = RADIO_BAND
    return lowpass(lowpass(highpass(highpass(samples, low), low), high),
                   high)


def static(rng: Random, n: int) -> Samples:
    hiss = radio(noise(rng, n))
    clicks = radio(crackle(rng, n, round(n / length(1.) * 8)))
    return mix((1., normalized(hiss)), (.4, normalized(clicks)))


def quindar(freq: float) -> Samples:
    n = length(QUINDAR)
    return faded(times(sine(freq, n), envelope(n, .005, 10.)), .005)


def talk(rng: Random, seconds: float) -> Samples:
    """ A distant voice, which can't be made out: syllables of noise
    through the formants of speech """
    out: Samples = []
    while len(out) < length(seconds):
        syllable = length(rng.uniform(.08, .22))
        voice = resonant(
            noise(rng, syllable), [rng.choice(FORMANTS)] * syllable, .15,
            band=True,
        )
        out += times(voice, envelope(syllable, .02, .05))
        if rng.random() < .25:
            out += [0.] * length(rng.uniform(.1, .3))   # a breath
    return radio(out)


def transmission(rng: Random, speaking: float) -> Samples:
    """ The opening tone, someone speaking, and the closing one, over the
    static of the radio """
    lead, tail = .15, .3
    voice = [.3 * s for s in normalized(talk(rng, speaking))] if (
        speaking
    ) else []
    message = [
        *[0.] * length(lead), *quindar(QUINDAR_OPEN),
        *[0.] * length(.15), *voice, *[0.] * length(.15),
        *quindar(QUINDAR_CLOSE), *[0.] * length(tail),
    ]
    n = len(message)
    hiss = times(static(rng, n), envelope(n, lead, 10.))
    return faded(mix((1., message), (.06, hiss)), tail)


def telemetry(
    rng: Random,
    freq: float,
    beeps: int,
    on: float,
    off: float
) -> Samples:
    """ Beeping, as satellites do """
    beep = times(sine(freq, length(on)), envelope(length(on), .005, 10.))
    beep = faded(beep, .005)
    signal: Samples = []
    for _ in range(beeps):
        signal += beep + [0.] * length(off)
    n = len(signal)
    return faded(mix((1., radio(signal)), (.05, static(rng, n))), .1)


def calls(rng: Random) -> dict[str, Samples]:
    """ The radio calls, by name """
    return {
        'radio_1': transmission(rng, 1.4),
        'radio_2': transmission(rng, 2.6),
        'radio_3': transmission(rng, 0.),
        'telemetry_1': telemetry(rng, 1800., 3, .06, .09),
        'telemetry_2': telemetry(rng, 950., 4, .3, .3),
    }
