""" The posts of the shuttle network, the Earth first """

from typing import TYPE_CHECKING

from ...logic.base.outposts import Outpost
from ...logic.base.quays import Quay
from ...logic.save import EARTH

if TYPE_CHECKING:
    from .earth_base import EarthBase


def quays_of(base: 'EarthBase', outposts: list[Outpost]) -> list[Quay]:
    assert base.player is not None
    return [
        Quay(EARTH, 'Terre', base.post, base.player.system.earth),
        *(
            Quay(outpost.key, outpost.name, outpost.post, outpost.body)
            for outpost in outposts
        ),
    ]
