""" Shuttles: each dock has one, carrying the minerals chosen from its depot
to the depot of another post, over and over, on its own """

from dataclasses import dataclass, field
from typing import Literal

from ..mining.ore import Hold, whole_units, withdraw
from .config import SHUTTLE_LOAD
from .unloading import depot_room

Leg = Literal['waiting', 'out', 'back']


@dataclass(frozen=True)
class Route:
    destination: str          # key of a post
    minerals: tuple[str, ...]


@dataclass(frozen=True)
class ShuttleState:
    """ As saved """
    route: Route | None = None
    leg: Leg = 'waiting'
    left: float = 0.
    trip: float = 0.
    load: Hold = field(default_factory=dict)


class Shuttle:

    def __init__(self) -> None:
        self.route: Route | None = None
        self.leg: Leg = 'waiting'
        self.left = 0.            # seconds of this trip
        self.trip = 0.            # seconds it takes
        self.load: Hold = {}

    def load_up(self, stock: Hold) -> None:
        """ Whole units of the minerals of its route, the first ones first """
        room = SHUTTLE_LOAD
        minerals = self.route.minerals if self.route else ()
        for name in minerals:
            units = min(whole_units(stock.get(name, 0.)), room)
            if units > 0:
                withdraw(stock, name, units)
                self.load[name] = float(units)
                room -= units

    def unload(self, stock: Hold) -> None:
        """ What fits, the rest going back """
        for name, units in list(self.load.items()):
            moved = min(units, depot_room(stock, name))
            if moved > 0:
                stock[name] = stock.get(name, 0.) + moved
                withdraw(self.load, name, moved)

    def update(self, dt: float, here: Hold, there: Hold | None,
               trip: float) -> None:
        """ `there` and `trip` being those of its route """
        if self.leg == 'waiting':
            if there is not None:
                self.load_up(here)
                if self.load:
                    self.leg, self.left, self.trip = 'out', trip, trip
            return
        self.left -= dt
        if self.left > 0:
            return
        if self.leg == 'out':
            if there is not None:
                self.unload(there)
            self.leg, self.left = 'back', self.trip
        else:
            self.unload(here)
            self.leg = 'waiting'

    @property
    def state(self) -> ShuttleState:
        return ShuttleState(
            self.route, self.leg, self.left, self.trip, dict(self.load),
        )

    def resume(self, state: ShuttleState) -> None:
        self.route, self.leg = state.route, state.leg
        self.left, self.trip = state.left, state.trip
        self.load = dict(state.load)
