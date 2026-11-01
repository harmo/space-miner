""" Shuttles: each dock has one, carrying the minerals chosen from its depot
to the depot of another post, over and over, on its own, once it can leave
full. It flies, see shuttle_flight.py. """

import math
from dataclasses import dataclass, field
from typing import Literal

from ..mining.ore import Hold, whole_units, withdraw
from ..world.space import Vec2
from .config import SHUTTLE_ARRIVAL, SHUTTLE_LOAD, SHUTTLE_SPEED
from .shuttle_flight import Airspace, fly, turned
from .unloading import depot_room

Leg = Literal['waiting', 'out', 'back']


@dataclass(frozen=True)
class Route:
    destination: str          # key of a post
    minerals: tuple[str, ...]


@dataclass(frozen=True)
class Way:
    """ The docks a shuttle flies between, as they are now """
    home: Vec2
    away: Vec2 | None         # None without a destination


@dataclass(frozen=True)
class ShuttleState:
    """ As saved """
    route: Route | None = None
    leg: Leg = 'waiting'
    offset: Vec2 | None = None
    heading: float = 0.
    load: Hold = field(default_factory=dict)


class Shuttle:

    def __init__(self) -> None:
        self.route: Route | None = None
        self.leg: Leg = 'waiting'
        self.offset: Vec2 | None = None     # from the sun, while flying
        self.heading = 0.
        self.load: Hold = {}

    @property
    def room(self) -> int:
        return SHUTTLE_LOAD - whole_units(sum(self.load.values()))

    def waiting_for(self, stock: Hold) -> int:
        """ Units of the minerals of its route, at most what it can take """
        minerals = self.route.minerals if self.route else ()
        return min(self.room, sum(
            whole_units(stock.get(name, 0.)) for name in minerals
        ))

    def load_up(self, stock: Hold) -> None:
        """ Whole units of the minerals of its route, the first ones first """
        room = self.room
        minerals = self.route.minerals if self.route else ()
        for name in minerals:
            units = min(whole_units(stock.get(name, 0.)), room)
            if units > 0:
                withdraw(stock, name, units)
                self.load[name] = self.load.get(name, 0.) + units
                room -= units

    def unload(self, stock: Hold) -> None:
        """ What fits, the rest going back """
        for name, units in list(self.load.items()):
            moved = min(units, depot_room(stock, name))
            if moved > 0:
                stock[name] = stock.get(name, 0.) + moved
                withdraw(self.load, name, moved)

    def arrive(self, here: Hold, there: Hold | None) -> None:
        if self.leg == 'out':
            if there is not None:
                self.unload(there)
            self.leg = 'back'
        else:
            self.unload(here)
            self.leg, self.offset = 'waiting', None

    def update(
        self,
        dt: float,
        here: Hold,
        there: Hold | None,
        way: Way,
        airspace: Airspace
    ) -> None:
        """ `there` and the way being those of its route """
        if self.leg == 'waiting':
            if there is not None and self.waiting_for(here) >= self.room:
                self.load_up(here)
                self.leg = 'out'
            return
        sun_x, sun_y = airspace.sun
        offset = self.offset
        pos = way.home if offset is None else (
            sun_x + offset[0], sun_y + offset[1],
        )
        goal = way.away if self.leg == 'out' and way.away else way.home
        step = SHUTTLE_SPEED * dt
        pos, angle = fly(pos, goal, airspace.obstacles, step)
        self.heading = turned(self.heading, angle, dt)
        self.offset = pos[0] - sun_x, pos[1] - sun_y
        if math.dist(pos, goal) <= step + SHUTTLE_ARRIVAL:
            self.arrive(here, there)

    @property
    def state(self) -> ShuttleState:
        return ShuttleState(
            self.route, self.leg, self.offset, self.heading, dict(self.load),
        )

    def resume(self, state: ShuttleState) -> None:
        self.route, self.leg = state.route, state.leg
        self.offset, self.heading = state.offset, state.heading
        self.load = dict(state.load)
