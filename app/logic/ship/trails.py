""" Exhaust trails: sparks thrown backwards from the nozzles while the ship
thrusts, looking after its engines. Sizes in pixels of the world. """

import math
from dataclasses import dataclass
from random import Random

from ..colors import Rgb
from ..world.space import Vec2
from .config import TRAIL_MAX
from .hulls import HULLS
from .parts import PARTS
from .shipyard import Design, center_of, part_rect


@dataclass(frozen=True)
class TrailStyle:
    start: Rgb                # color when thrown
    end: Rgb                  # when fading out
    width: float              # of a spark when thrown
    life: float               # seconds
    speed: float              # thrown backwards, relative to the ship
    spread: float             # degrees, of the cone they are thrown in
    rate: float               # sparks per second, at full thrust


NOZZLE = 'hull'               # the hull's own, without an engine
TRAILS = {
    NOZZLE: TrailStyle((1., .75, .4), (.6, .2, .1), 2.5, .35, 60., 12., 40.),
    'engine': TrailStyle(
        (1., .85, .45), (1., .3, .1), 4., .5, 90., 10., 60.,
    ),
    'twin_engine': TrailStyle(
        (1., .85, .45), (1., .3, .1), 4., .55, 95., 9., 50.,
    ),
    'afterburner': TrailStyle(
        (1., 1., .85), (1., .45, .15), 5., .7, 140., 6., 80.,
    ),
    'ion_engine': TrailStyle(
        (.75, .95, 1.), (.2, .5, 1.), 3., .9, 110., 3., 70.,
    ),
    'vector_nozzle': TrailStyle(
        (1., .95, .7), (.9, .5, .2), 3., .3, 70., 25., 50.,
    ),
    'fusion_engine': TrailStyle(
        (.9, .85, 1.), (.55, .4, 1.), 6., .8, 120., 5., 90.,
    ),
    # Not an engine: sparkles drifting off the panels
    'solar_sail': TrailStyle(
        (1., .95, .6), (.6, .8, 1.), 1.5, 1.2, 30., 60., 25.,
    ),
}
# Engines with two nozzles, across them
TWIN_NOZZLES = {'twin_engine': (.25, .75)}

Nozzle = tuple[Vec2, str]     # from the center of the ship, and its trail


def nozzles(design: Design) -> list[Nozzle]:
    """ At the back of what each rear slot holds, or of the hull """
    hull = HULLS[design.hull]
    cx, cy = center_of(design)
    found: list[Nozzle] = []
    for slot_id, slot in hull.slots.items():
        if slot.kind != 'rear':
            continue
        part_id = design.parts.get(slot_id)
        if part_id is None:
            found.append(((-hull.size[0] / 2 - cx, slot.anchor[1] - cy),
                          NOZZLE))
            continue
        x, y, _, height = part_rect(slot, PARTS[part_id])
        style = part_id if part_id in TRAILS else NOZZLE
        for across in TWIN_NOZZLES.get(part_id, (.5,)):
            found.append(((x - cx, y + height * across - cy), style))
    return found


@dataclass(slots=True)
class Spark:
    x: float
    y: float
    vx: float
    vy: float
    style: TrailStyle
    age: float = 0.

    @property
    def done(self) -> bool:
        return self.age >= self.style.life


def look(spark: Spark) -> tuple[Rgb, float, float]:
    """ Color, opacity and size: fading out and shrinking with age """
    style = spark.style
    t = min(1., spark.age / style.life)
    color = (
        style.start[0] + (style.end[0] - style.start[0]) * t,
        style.start[1] + (style.end[1] - style.start[1]) * t,
        style.start[2] + (style.end[2] - style.start[2]) * t,
    )
    return color, .9 * (1 - t) ** 1.5, style.width * (1 - .6 * t)


class Trail:
    """ The sparks of all the nozzles of a ship """

    def __init__(self, rng: Random) -> None:
        self.rng = rng
        self.sparks: list[Spark] = []
        self.owed: list[float] = []     # sparks not thrown yet, by nozzle

    def update(
        self,
        dt: float,
        pos: Vec2,
        angle: float,
        velocity: Vec2,
        ship_nozzles: list[Nozzle],
        thrust: float
    ) -> None:
        """ Throws sparks for `thrust`, from 0 to 1 """
        for spark in self.sparks:
            spark.age += dt
            spark.x += spark.vx * dt
            spark.y += spark.vy * dt
        self.sparks[:] = [spark for spark in self.sparks if not spark.done]
        if len(self.owed) != len(ship_nozzles):
            self.owed = [0.] * len(ship_nozzles)
        if thrust <= 0:
            return
        cos, sin = math.cos(angle), math.sin(angle)
        for index, ((x, y), name) in enumerate(ship_nozzles):
            style = TRAILS[name]
            self.owed[index] += style.rate * thrust * dt
            nozzle = (pos[0] + x * cos - y * sin, pos[1] + x * sin + y * cos)
            while self.owed[index] >= 1:
                self.owed[index] -= 1
                self.throw(nozzle, angle, velocity, style, dt)
        del self.sparks[:-TRAIL_MAX]

    def throw(
        self,
        nozzle: Vec2,
        angle: float,
        velocity: Vec2,
        style: TrailStyle,
        dt: float
    ) -> None:
        rng = self.rng
        spread = math.radians(style.spread) / 2
        backwards = angle + math.pi + rng.uniform(-spread, spread)
        speed = style.speed * rng.uniform(.7, 1.3)
        vx = velocity[0] + math.cos(backwards) * speed
        vy = velocity[1] + math.sin(backwards) * speed
        # Spread along the way they went during the frame, not in clumps
        early = rng.uniform(0, dt)
        self.sparks.append(Spark(
            nozzle[0] + vx * early, nozzle[1] + vy * early, vx, vy, style,
            early,
        ))

    def shift(self, shift: Vec2) -> None:
        for spark in self.sparks:
            spark.x += shift[0]
            spark.y += shift[1]
