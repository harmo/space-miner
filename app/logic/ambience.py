""" The ambience of space: drones fading into one another at random, and
radio calls now and then over them """

import math
from random import Random

DRONES = tuple(f'drone_{number}' for number in range(1, 11))
CALLS = ('radio_1', 'radio_2', 'radio_3', 'telemetry_1', 'telemetry_2')
DRONE_HOLD = (90., 180.)      # seconds a drone plays alone
DRONE_FADE = 12.              # seconds fading into the next one
CALL_EVERY = (30., 90.)       # seconds between radio calls


class Ambience:
    """ The next drone is picked as soon as the current one plays, to be
    ready when their fade comes """

    def __init__(self, rng: Random) -> None:
        self.rng = rng
        self.current = rng.choice(DRONES)
        self.upcoming = self.pick()
        self.alone = rng.uniform(*DRONE_HOLD)   # seconds left before fading
        self.fading = 0.                        # seconds into the fade
        self.call_in = rng.uniform(*CALL_EVERY)

    def pick(self) -> str:
        """ Any drone but the current one """
        return self.rng.choice(
            [drone for drone in DRONES if drone != self.current]
        )

    def update(self, dt: float) -> None:
        if self.alone > 0:
            self.alone -= dt
            return
        self.fading += dt
        if self.fading >= DRONE_FADE:
            self.current = self.upcoming
            self.upcoming = self.pick()
            self.alone = self.rng.uniform(*DRONE_HOLD)
            self.fading = 0.

    @property
    def volumes(self) -> dict[str, float]:
        """ Of the drones heard, by name: the sum of their powers stays
        the same while fading, so the ambience neither swells nor dips """
        if self.alone > 0:
            return {self.current: 1.}
        angle = min(1., self.fading / DRONE_FADE) * math.pi / 2
        return {self.current: math.cos(angle), self.upcoming: math.sin(angle)}

    def call(self, dt: float) -> str | None:
        """ A radio call, once in a while """
        self.call_in -= dt
        if self.call_in > 0:
            return None
        self.call_in = self.rng.uniform(*CALL_EVERY)
        return self.rng.choice(CALLS)
