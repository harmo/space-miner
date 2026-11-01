""" What is going on around the solar system, as saved: it comes back as
it was, those asteroids still there at the same place on their orbits """

from dataclasses import dataclass, field

from .flares import Phase
from .layout import OrbiterPlan
from .space import Vec2


@dataclass(frozen=True)
class LostCanister:
    """ Lost in a crash, from what it floats around """
    mineral: str
    amount: float
    altitude: float           # of its orbit, around a planet
    around: int               # among the bodies pulling, the sun first
    offset: Vec2              # from it


@dataclass(frozen=True)
class CometState:
    anomaly: float            # along its way
    tilt: float
    sense: int
    shed: int                 # asteroids, mined or not
    debris: list[OrbiterPlan] = field(default_factory=list)


@dataclass(frozen=True)
class EventsState:
    flare_phase: Phase
    flare_left: float         # seconds of that phase
    ejecta: list[OrbiterPlan]
    swarm_waiting: float      # seconds
    swarm_left: float
    swarm: list[OrbiterPlan]
    comet_waiting: float
    comet: CometState | None = None
