""" Mining lasers, by level: a better one mines what weaker ones can't, and
faster, with a beam that shows it """

from dataclasses import dataclass

from ..colors import Rgb


@dataclass(frozen=True)
class Laser:
    power: float              # times the mining speed of the first level
    color: Rgb
    width: float              # of the beam, in screen pixels
    halo: bool = False        # wide translucent glow around the beam
    core: bool = False        # white hot center
    burn: float = 0.          # fuel a second, while firing


LASERS = (
    Laser(1., (1., .35, .3), 1.5, burn=.4),
    Laser(2., (1., .62, .25), 2.2, halo=True, burn=.6),
    Laser(3.5, (1., .88, .4), 3., halo=True, core=True, burn=.8),
    Laser(5., (.78, .55, 1.), 4., halo=True, core=True, burn=1.),
    # Beyond what any mineral needs: only faster
    Laser(7., (.6, .95, 1.), 5., halo=True, core=True, burn=1.2),
)
BEST = len(LASERS)


def laser(level: int) -> Laser:
    """ Levels beyond the best one are as good as it """
    return LASERS[max(1, min(level, len(LASERS))) - 1]
