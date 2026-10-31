""" Layout of the solar system, drawn at random when the game starts """

import math
from collections.abc import Sequence
from dataclasses import dataclass
from random import Random

from ..config import CERES, MOON, STATION
from ..mining.minerals import ASTEROID_SHAPES, MINERALS, asteroid_texture
from .config import (
    ASTEROID_MASS,
    ASTEROID_RADIUS,
    ASTEROID_SPIN,
    BELT_AFTER,
    BELT_ASTEROIDS,
    BELT_COUNT,
    BELT_SPEED,
    BELT_WIDTH,
    CERES_BELT_ASTEROIDS,
    CERES_BELT_ORBITS,
    CERES_BELT_SPEED,
    CERES_GRAVITY,
    CERES_RADIUS,
    CERES_REGROW_TIME,
    EARTH_ORBIT,
    FIRST_ORBIT,
    GAP_SPREAD,
    GRAVITY,
    LINEUP,
    MOON_MASS,
    MOON_ORBIT,
    MOON_RADIUS,
    MOON_SPEED,
    ORBIT_GAPS,
    PLANET_MASS,
    PLANET_SPEED,
    REGROW_THRESHOLD,
    REGROW_TIME,
    STATION_ALTITUDE,
    STATION_RADIUS,
    STATION_SPEED,
    SUN_BELT_ASTEROIDS,
    SUN_BELT_SPEED,
    SUN_BELT_WIDTH,
)

CERES_PARENT = -1             # not a planet, see BeltPlan


@dataclass(frozen=True, slots=True)
class OrbiterPlan:
    """ A body put on a circular orbit around its parent """
    texture: str
    radius: float
    mass: float
    orbit_radius: float
    speed: float               # along the orbit, negative to go clockwise
    orbit_angle: float         # starting position on the orbit (radians)
    rotation: float = 0.       # starting angle of the body itself (radians)
    spin: float = 0.           # degrees/s
    gravity: float = 0.        # pull at its surface (px/s²)
    mineral: str | None = None  # for asteroids
    # Turning as fast as it goes round, the same face to its parent
    locked: bool = False


@dataclass(frozen=True, slots=True)
class PlanetPlan:
    planet: OrbiterPlan
    satellites: tuple[OrbiterPlan, ...] = ()   # the moon, or a belt

    @property
    def extent(self) -> float:
        """ Distance from the planet center to its farthest edge, satellites
        included """
        return max(
            [self.planet.radius]
            + [s.orbit_radius + s.radius for s in self.satellites]
        )


@dataclass(frozen=True, slots=True)
class BeltPlan:
    """ Where the asteroids of a belt turn, to put back those mined """
    # Index of its planet, CERES_PARENT around Cérès, None around the sun
    parent: int | None
    orbits: tuple[float, float]   # from the center of its parent
    # In px/s, or around the sun times the speed of a planet at that distance
    speeds: tuple[float, float]
    full: int
    regrow_time: float = REGROW_TIME
    regrow_below: float = REGROW_THRESHOLD   # of `full`

    def asteroid(self, rng: Random,
                 angle: float | None = None) -> OrbiterPlan:
        distance = rng.uniform(*self.orbits)
        speed = rng.uniform(*self.speeds)
        if self.parent is None:
            speed *= orbital_speed(distance)
        return plan_asteroid(rng, distance, speed, angle)


@dataclass(frozen=True, slots=True)
class SystemPlan:
    planets: tuple[PlanetPlan, ...]   # from the sun outwards
    earth: int                       # index of the Earth in planets
    sun_belt: tuple[OrbiterPlan, ...]
    belts: tuple[BeltPlan, ...]      # those of the planets, then the sun's
    # Distances to the sun of the planets, and of the belt around it, which
    # comes after BELT_AFTER planets
    orbits: tuple[float, ...]


def plan_orbits(rng: Random) -> tuple[float, ...]:
    """ Wider and wider apart outwards, each game a little differently """
    orbits = [FIRST_ORBIT]
    for gap in ORBIT_GAPS:
        orbits.append(orbits[-1] + gap * rng.uniform(*GAP_SPREAD))
    return tuple(orbits)


def planet_orbits(orbits: tuple[float, ...]) -> tuple[float, ...]:
    """ The orbits of the planets, without the belt's one """
    return orbits[:BELT_AFTER + 1] + orbits[BELT_AFTER + 2:]


def sun_belt_orbit(orbits: tuple[float, ...]) -> float:
    """ Middle of the belt around the sun """
    return orbits[BELT_AFTER + 1]


def orbital_speed(distance: float) -> float:
    """ Like real planets, the farther the slower """
    return PLANET_SPEED * math.sqrt(FIRST_ORBIT / distance)


def plan_system(rng: Random) -> SystemPlan:
    orbits = plan_orbits(rng)
    distances = planet_orbits(orbits)
    # Not around the first planet, the refuge of its station stays safe
    others = [i for i in range(1, len(LINEUP)) if i != EARTH_ORBIT]
    belts = set(rng.sample(others, BELT_COUNT))

    planets = []
    belt_plans = []
    for index, (texture, radius) in enumerate(LINEUP):
        if index == EARTH_ORBIT:
            satellites: tuple[OrbiterPlan, ...] = (plan_moon(rng),)
        else:
            satellites = ()
            if index in belts:
                belt = planet_belt(rng, index, radius)
                belt_plans.append(belt)
                satellites = tuple(
                    belt.asteroid(rng) for _ in range(belt.full)
                )
        distance = distances[index]
        # Upright and not spinning, a landed ship stays where it is
        planet = OrbiterPlan(
            texture, radius, PLANET_MASS, distance,
            speed=orbital_speed(distance),
            orbit_angle=rng.uniform(0, 2 * math.pi),
            gravity=GRAVITY * radius,
        )
        planets.append(PlanetPlan(planet, satellites))
    sun_belt = plan_sun_belt(sun_belt_orbit(orbits))
    belt_plans.append(sun_belt)
    return SystemPlan(
        tuple(planets), EARTH_ORBIT,
        tuple(sun_belt.asteroid(rng) for _ in range(sun_belt.full)),
        tuple(belt_plans), orbits,
    )


def plan_ceres(orbits: tuple[float, ...],
               earth_angle: float) -> OrbiterPlan:
    """ In the middle of the belt around the sun, across the sun from the
    Earth at first. Upright and not spinning, as planets: a landed ship
    stays where it is. """
    distance = sun_belt_orbit(orbits)
    return OrbiterPlan(
        CERES, CERES_RADIUS, PLANET_MASS, distance,
        speed=orbital_speed(distance), orbit_angle=earth_angle + math.pi,
        gravity=CERES_GRAVITY,
    )


def plan_ceres_belt() -> BeltPlan:
    """ Asteroids turning around Cérès, always there """
    return BeltPlan(
        CERES_PARENT, CERES_BELT_ORBITS, CERES_BELT_SPEED,
        CERES_BELT_ASTEROIDS, CERES_REGROW_TIME, 1.,
    )


def plan_station(planet_radius: float) -> OrbiterPlan:
    """ Around a planet, not spinning, pulling nothing: drawn over the game,
    its body unseen """
    return OrbiterPlan(
        STATION, STATION_RADIUS, PLANET_MASS,
        planet_radius + STATION_ALTITUDE, STATION_SPEED, orbit_angle=0.,
    )


def plan_moon(rng: Random) -> OrbiterPlan:
    """ Locked, like the real one: the same face to the Earth """
    angle = rng.uniform(0, 2 * math.pi)
    return OrbiterPlan(
        MOON, MOON_RADIUS, MOON_MASS, MOON_ORBIT, MOON_SPEED,
        orbit_angle=angle, rotation=facing(angle),
        spin=math.degrees(MOON_SPEED / MOON_ORBIT), locked=True,
    )


def facing(orbit_angle: float) -> float:
    """ Angle of a body on its orbit, turned towards its parent """
    return orbit_angle + math.pi


def plan_asteroid(rng: Random, orbit_radius: float, speed: float,
                  angle: float | None = None,
                  minerals: Sequence[str] = tuple(MINERALS),
                  radius: tuple[float, float] = ASTEROID_RADIUS,
                  ) -> OrbiterPlan:
    """ Of a mineral as common as it is among `minerals`, at `angle` on its
    orbit or anywhere """
    mineral = rng.choices(
        minerals, weights=[MINERALS[name].frequency for name in minerals]
    )[0]
    return OrbiterPlan(
        asteroid_texture(mineral, rng.choice(ASTEROID_SHAPES)),
        rng.uniform(*radius),
        ASTEROID_MASS,
        orbit_radius,
        speed,
        orbit_angle=(
            rng.uniform(0, 2 * math.pi) if angle is None else angle
        ),
        rotation=rng.uniform(0, 2 * math.pi),
        spin=rng.uniform(-ASTEROID_SPIN, ASTEROID_SPIN),
        mineral=mineral,
    )


def planet_belt(rng: Random, index: int, radius: float) -> BeltPlan:
    """ Asteroids all turning the same way around a planet """
    direction = rng.choice((-1, 1))
    low, high = BELT_SPEED
    return BeltPlan(
        index, (radius + BELT_WIDTH[0], radius + BELT_WIDTH[1]),
        (direction * low, direction * high), BELT_ASTEROIDS,
    )


def plan_sun_belt(middle: float) -> BeltPlan:
    """ Sparse asteroids turning around the sun like the planets """
    return BeltPlan(
        None, (middle - SUN_BELT_WIDTH / 2, middle + SUN_BELT_WIDTH / 2),
        SUN_BELT_SPEED, SUN_BELT_ASTEROIDS,
    )
