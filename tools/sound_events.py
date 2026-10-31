""" Sounds of what happens, each with its length and its loudness """

from collections.abc import Callable
from dataclasses import dataclass
from random import Random

from .synth import Samples, faded, length, level

# Loudness, in decibels, from the laser, which sounds right in the game:
# the other loops stay below it, as do sounds of events at their loudest
LASER_DB = -26.
LOOP_DB = -32.
EVENT_DB = -28.
FLARE_DB = -26.               # the sun blasting, above everything
BREAK_DB = -34.               # heard again and again while mining
CLICK_DB = -34.               # heard so often it must stay discreet
AMBIENT_DB = -30.             # always there, its volume set apart
RADIO_DB = -36.               # calls now and then over the ambience
EVENT_WINDOW = .1             # seconds, their loudness is measured over
FADE = .4                     # seconds, at their end


@dataclass(frozen=True)
class SoundEvent:
    seconds: float
    compose: Callable[[Random, int], Samples]
    db: float = EVENT_DB

    def render(self, rng: Random) -> Samples:
        seconds = self.seconds
        sound = faded(self.compose(rng, length(seconds)),
                      min(FADE, seconds / 3))
        return level(sound, self.db, EVENT_WINDOW)
