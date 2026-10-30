""" Sound synthesis: waves, noise and filters on plain lists of samples
between -1 and 1, brought to a chosen loudness and saved as Ogg Vorbis
files, encoded by ffmpeg. Loops repeat seamlessly when their frequencies
make whole cycles over them, see `looping`, and when they are filtered as
loops: the encoding keeps their length to the sample. """

import array
import io
import math
import subprocess
import wave
from pathlib import Path
from random import Random

RATE = 44100                  # samples per second
PEAK = .9                     # the loudest a sample may get
QUALITY = 5                   # of the encoding, from 0 to 10

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


def twice(samples: Samples, loop: bool) -> Samples:
    """ What a filter runs over: a loop twice over, so that it ends as it
    starts, see `settled` """
    return samples * 2 if loop else samples


def settled(out: Samples, n: int) -> Samples:
    """ The last `n` samples, once a filter settled over a loop """
    return out[len(out) - n:]


def resonant(samples: Samples, cutoff: Samples, damping: float,
             loop: bool = False, band: bool = False) -> Samples:
    """ The filter of modular synthesizers, its cutoff moving along
    `cutoff`, in Hz, sample after sample: a low pass, or a band pass
    around it. It rings at its cutoff with a low `damping`, from 2 down
    to 0.1 or so. """
    tuning = [2 * math.sin(math.pi * min(hz, RATE / 6) / RATE)
              for hz in cutoff]
    low = middle = 0.
    out = []
    n = len(samples)
    for i, sample in enumerate(twice(samples, loop)):
        f = tuning[i % n]
        low += f * middle
        middle += f * (sample - low - damping * middle)
        out.append(middle if band else low)
    return settled(out, n)


def echo(samples: Samples, seconds: float, feedback: float,
         loop: bool = False) -> Samples:
    """ Repeating every `seconds`, each time `feedback` as loud """
    gap = length(seconds)
    out: Samples = []
    for i, sample in enumerate(twice(samples, loop)):
        out.append(sample + (feedback * out[i - gap] if i >= gap else 0.))
    return settled(out, len(samples))


def reverb(samples: Samples, wet: float, loop: bool = False) -> Samples:
    """ A room, `wet` the share of its reflections: echoes of combs out of
    step with one another, smeared by all pass filters """
    source = twice(samples, loop)
    combs = []
    for gap in (1557, 1617, 1491, 1422, 1277, 1356):
        out: Samples = []
        soft = 0.
        for i, sample in enumerate(source):
            back = out[i - gap] if i >= gap else 0.
            soft += .4 * (back - soft)          # walls soften the highs
            out.append(sample + .84 * soft)
        combs.append(out)
    wash = [sum(values) / len(combs) for values in zip(*combs, strict=True)]
    for gap in (556, 441, 341, 225):
        smeared: Samples = []
        for i, sample in enumerate(wash):
            if i >= gap:
                smeared.append(
                    wash[i - gap] + .5 * smeared[i - gap] - .5 * sample
                )
            else:
                smeared.append(-.5 * sample)
        wash = smeared
    room = settled(wash, len(samples))
    return [(1 - wet) * dry + wet * reflected
            for dry, reflected in zip(samples, room, strict=True)]


def placed(sound: Samples, n: int, seconds: float) -> Samples:
    """ `n` samples long, `sound` starting `seconds` in and wrapping around
    to the start: in a loop """
    out = [0.] * n
    start = length(seconds)
    for k, sample in enumerate(sound):
        out[(start + k) % n] += sample
    return out


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
    """ Mono, at `path` ending in .ogg. The same samples always make the
    same file, whatever the version of ffmpeg. """
    data = array.array('h', (round(sample * 32767) for sample in samples))
    source = io.BytesIO()
    with wave.open(source, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(data.tobytes())
    subprocess.run(
        [
            'ffmpeg', '-loglevel', 'error', '-y', '-f', 'wav', '-i', '-',
            '-c:a', 'libvorbis', '-q:a', str(QUALITY),
            '-fflags', '+bitexact', '-flags:a', '+bitexact', str(path),
        ],
        input=source.getvalue(), check=True,
    )
