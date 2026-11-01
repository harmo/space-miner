""" Belts growing back: once mined below a threshold, they get asteroids
back one at a time, until full again. A threshold of 1 keeps them full. """

from .config import REGROW_THRESHOLD, REGROW_TIME


class Regrowth:

    def __init__(
        self,
        full: int,
        time: float = REGROW_TIME,
        threshold: float = REGROW_THRESHOLD
    ) -> None:
        self.full = full
        self.time = time          # for the whole belt to grow back
        self.threshold = threshold  # part of `full` it starts below
        self.growing = False
        self.waited = 0.          # since the last asteroid came back

    @property
    def period(self) -> float:
        """ Between two asteroids """
        return self.time / self.full

    def update(self, count: int, dt: float) -> int:
        """ How many asteroids come back now, for a belt holding `count` """
        if count >= self.full:
            self.growing = False
            self.waited = 0.
            return 0
        if count < self.full * self.threshold:
            self.growing = True
        if not self.growing:
            return 0
        self.waited += dt
        coming = int(self.waited // self.period)
        self.waited -= coming * self.period
        return min(coming, self.full - count)
