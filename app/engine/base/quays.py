""" The posts of the shuttle network, the Earth first """

import math
from typing import TYPE_CHECKING

from ...logic.base.outposts import Outpost
from ...logic.base.quays import Quay
from ...logic.save import EARTH
from ...logic.ship.config import START_DIRECTION

if TYPE_CHECKING:
    from .earth_base import EarthBase


# Beside the ship coming out of the hangar
EARTH_DOCK = math.radians(START_DIRECTION) + .7


def quays_of(base: 'EarthBase', outposts: list[Outpost]) -> list[Quay]:
    assert base.player is not None
    return [
        Quay(EARTH, 'Terre', base.post, base.player.system.earth, EARTH_DOCK),
        *(
            Quay(
                outpost.key, outpost.name, outpost.post, outpost.body,
                outpost.dock_direction,
            )
            for outpost in outposts
        ),
    ]
