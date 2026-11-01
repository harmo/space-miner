""" The posts of the solar system as a network of shuttles: where they can
go, how long it takes, and where they are """

import math
from collections.abc import Sequence
from dataclasses import dataclass

from ..world.space import Celestial, Vec2
from .config import SHUTTLE_MIN_TRIP, SHUTTLE_SPEED
from .post import Post


@dataclass(frozen=True)
class Quay:
    """ A post on the shuttle network """
    key: str
    name: str
    post: Post
    body: Celestial

    @property
    def docks(self) -> bool:
        return self.post.services.dock

    @property
    def takes(self) -> bool:
        """ Shuttles can come: it has a depot """
        return self.post.services.depot


def can_send(quay: Quay, quays: Sequence[Quay]) -> bool:
    """ It has a dock, and another post a depot to send ore to """
    return quay.docks and any(
        other.takes for other in quays if other is not quay
    )


def trip_time(start: Quay, end: Quay) -> float:
    """ Seconds one way, from where they are now """
    distance = math.dist(start.body.pos, end.body.pos)
    return max(SHUTTLE_MIN_TRIP, distance / SHUTTLE_SPEED)


def destination_of(quay: Quay, quays: Sequence[Quay]) -> Quay | None:
    route = quay.post.shuttle.route
    if route is None:
        return None
    return next(
        (q for q in quays if q.key == route.destination and q.takes), None,
    )


def update_shuttles(quays: Sequence[Quay], dt: float) -> None:
    """ Those of the docks built """
    for quay in quays:
        if quay.docks:
            target = destination_of(quay, quays)
            quay.post.shuttle.update(
                dt, quay.post.depot.stock,
                target.post.depot.stock if target else None,
                trip_time(quay, target) if target else 0.,
            )


def shuttle_position(quay: Quay, quays: Sequence[Quay]) -> Vec2 | None:
    """ Between the two posts, None when not on its way """
    shuttle = quay.post.shuttle
    target = destination_of(quay, quays)
    if shuttle.leg == 'waiting' or target is None or shuttle.trip <= 0:
        return None
    done = 1 - shuttle.left / shuttle.trip
    share = done if shuttle.leg == 'out' else 1 - done
    x, y = quay.body.pos
    end_x, end_y = target.body.pos
    return x + (end_x - x) * share, y + (end_y - y) * share
