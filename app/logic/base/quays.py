""" The posts of the solar system as a network of shuttles: where they can
go, where their docks are, and the shuttles on their way """

import math
from collections.abc import Sequence
from dataclasses import dataclass

from ..mining.minerals import MINERALS
from ..mining.ore import Hold, whole_units
from ..world.space import Celestial, Vec2
from .config import SHUTTLE_DOCK_HEIGHT
from .post import Post
from .shuttle_flight import Airspace
from .shuttles import Way


@dataclass(frozen=True)
class Quay:
    """ A post on the shuttle network """
    key: str
    name: str
    post: Post
    body: Celestial
    direction: float = 0.     # of its dock, from the body center

    @property
    def docks(self) -> bool:
        return self.post.services.dock

    @property
    def berths(self) -> bool:
        """ A pad can be seen there """
        return self.docks or self.post.services.berth

    @property
    def takes(self) -> bool:
        """ Shuttles can come: it has a depot """
        return self.post.services.depot

    @property
    def spot(self) -> Vec2:
        """ Where its shuttle stands """
        x, y = self.body.pos
        distance = self.body.radius + SHUTTLE_DOCK_HEIGHT
        return (
            x + math.cos(self.direction) * distance,
            y + math.sin(self.direction) * distance,
        )


@dataclass(frozen=True)
class ShuttleMark:
    """ A shuttle on its way, as the map tells it """
    pos: Vec2
    way: str                  # from where to where
    carried: str


def can_send(quay: Quay, quays: Sequence[Quay]) -> bool:
    """ It has a dock, and another post a depot to send ore to """
    return quay.docks and any(
        other.takes for other in quays if other is not quay
    )


def destination_of(quay: Quay, quays: Sequence[Quay]) -> Quay | None:
    route = quay.post.shuttle.route
    if route is None:
        return None
    return next(
        (q for q in quays if q.key == route.destination and q.takes), None,
    )


def update_shuttles(
    quays: Sequence[Quay],
    airspace: Airspace,
    dt: float
) -> None:
    """ Those of the docks built """
    for quay in quays:
        if quay.docks:
            target = destination_of(quay, quays)
            quay.post.shuttle.update(
                dt, quay.post.depot.stock,
                target.post.depot.stock if target else None,
                Way(quay.spot, target.spot if target else None), airspace,
            )


def shuttle_position(quay: Quay, sun: Vec2) -> Vec2 | None:
    """ None when not on its way """
    offset = quay.post.shuttle.offset
    if offset is None:
        return None
    return sun[0] + offset[0], sun[1] + offset[1]


def carried_text(load: Hold) -> str:
    return ' · '.join(
        f'{whole_units(load[name])} {mineral.name}'
        for name, mineral in MINERALS.items() if name in load
    ) or 'À vide'


def shuttle_marks(quays: Sequence[Quay], sun: Vec2) -> list[ShuttleMark]:
    """ Those on their way """
    marks = []
    for quay in quays:
        pos = shuttle_position(quay, sun)
        if pos is not None:
            target = destination_of(quay, quays)
            shuttle = quay.post.shuttle
            away = target.name if target else '?'
            start, end = (
                (quay.name, away) if shuttle.leg == 'out'
                else (away, quay.name)
            )
            marks.append(ShuttleMark(
                pos, f'{start} vers {end}', carried_text(shuttle.load),
            ))
    return marks
