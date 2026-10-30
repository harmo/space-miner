""" Sound synthesis: waves, noise and filters on plain lists of samples
between -1 and 1, brought to a chosen loudness and saved as WAV files.
Loops repeat seamlessly when their frequencies make whole cycles over
them, see `looping`, and when they are filtered as loops. """

import array
import math
import wave
from pathlib import Path
from random import Random

RATE = 44100                  # samples per second
PEAK = .9                     # the loudest a sample may get

Samples = list[float]


def length(seconds: float) -> int:
    return round(seconds * RATE)


def looping(freq: float, seconds: float) -> float:
    """ The closest frequency making whole cycles over `seconds` """
    return max(1, round(freq * seconds)) / seconds


def sine(freq: float, n: int) -> Samples:
    step = 2 * math.pi * freq / RATE
    return [math.sin(step * i) for i in range(n)]


def saw(freq: float, n: int) -> Samples:
    step = freq / RATE
    return [(step * i) % 1 * 2 - 1 for i in range(n)]


def glide(start: float, end: float, n: int) -> Samples:
    """ Sine sliding from `start` to `end` Hz """
    out = []
    phase = 0.
    for i in range(n):
        out.append(math.sin(phase))
        phase += 2 * math.pi * start * (end / start) ** (i / n) / RATE
    return out


def envelope(n: int, attack: float, decay: float) -> Samples:
    """ Rising in `attack` seconds, then fading by e every `decay` """
    rise = max(1, length(attack))
    fall = decay * RATE
    return [
        i / rise if i < rise else math.exp(-(i - rise) / fall)
        for i in range(n)
    ]


def ring(freq: float, n: int, decay: float,
         attack: float = .002) -> Samples:
    """ Struck, then fading """
    return times(sine(freq, n), envelope(n, attack, decay))


def faded(samples: Samples, seconds: float) -> Samples:
    """ Fading out over its last `seconds`, not to end with a click """
    size = min(length(seconds), len(samples))
    start = len(samples) - size
    return samples[:start] + [
        sample * (1 - k / size) ** 2
        for k, sample in enumerate(samples[start:])
    ]


def delayed(samples: Samples, seconds: float) -> Samples:
    """ As long, starting `seconds` later """
    start = min(length(seconds), len(samples))
    return [0.] * start + samples[:len(samples) - start]


def noise(rng: Random, n: int) -> Samples:
    return [rng.uniform(-1, 1) for _ in range(n)]


def crackle(rng: Random, n: int, count: int,
            decay: float = .0015) -> Samples:
    """ `count` clicks of random strength, fading in `decay` seconds, those
    at the end wrapping around to the start """
    out = [0.] * n
    fade = decay * RATE
    for _ in range(count):
        start = rng.randrange(n)
        strength = rng.uniform(.2, 1)
        for k in range(round(fade * 5)):
            out[(start + k) % n] += (
                strength * rng.uniform(-1, 1) * math.exp(-k / fade)
            )
    return out


def lowpass(samples: Samples, cutoff: float, loop: bool = False) -> Samples:
    """ Softens what is above `cutoff` Hz. A loop is filtered twice over,
    so that it ends as it starts. """
    a = 1 - math.exp(-2 * math.pi * cutoff / RATE)
    source = samples * 2 if loop else samples
    y = 0.
    out = []
    for sample in source:
        y += a * (sample - y)
        out.append(y)
    return out[len(out) - len(samples):]


def highpass(samples: Samples, cutoff: float,
             loop: bool = False) -> Samples:
    """ Softens what is below `cutoff` Hz """
    low = lowpass(samples, cutoff, loop)
    return [sample - soft for sample, soft in zip(samples, low, strict=True)]


def mix(*layers: tuple[float, Samples]) -> Samples:
    """ Sum of the layers, each times its weight """
    out = [0.] * max(len(samples) for _, samples in layers)
    for weight, samples in layers:
        for i, sample in enumerate(samples):
            out[i] += weight * sample
    return out


def times(samples: Samples, by: Samples) -> Samples:
    return [sample * k for sample, k in zip(samples, by, strict=True)]


def throb(freq: float, n: int, depth: float) -> Samples:
    """ Between 1 - `depth` and 1, `freq` times a second """
    step = 2 * math.pi * freq / RATE
    return [1 - depth * (.5 + .5 * math.sin(step * i)) for i in range(n)]


def loudness(samples: Samples, window: float | None = None) -> float:
    """ Root mean square, in decibels below a full scale wave: of its
    loudest `window` seconds if given, for sounds fading away """
    size = length(window) if window else len(samples)
    rms = max(
        math.sqrt(
            sum(sample * sample for sample in samples[start:start + size])
            / size
        )
        for start in range(0, max(1, len(samples) - size + 1), size // 4)
    )
    return 20 * math.log10(max(rms, 1e-9))


def normalized(samples: Samples) -> Samples:
    """ At a root mean square of 1, so layers mix in the weights given """
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    return [sample / max(rms, 1e-9) for sample in samples]


def level(samples: Samples, db: float,
          window: float | None = None) -> Samples:
    """ At `db` loudness, quieter if its peaks would get beyond PEAK """
    gain = 10 ** ((db - loudness(samples, window)) / 20)
    peak = max(abs(sample) for sample in samples) * gain
    if peak > PEAK:
        gain *= PEAK / peak
    return [sample * gain for sample in samples]


def save(path: Path, samples: Samples) -> None:
    """ 16 bit mono """
    data = array.array('h', (round(sample * 32767) for sample in samples))
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(data.tobytes())
