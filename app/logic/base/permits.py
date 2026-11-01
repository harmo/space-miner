""" Concessions: big missions given on the Earth, one for each of the
stages of outposts worth more than the others, which can't be built until
it is validated """

from collections.abc import Sequence
from dataclasses import dataclass

from ..mining.ore import Hold
from .board import Board
from .missions import Mission, take


@dataclass(frozen=True)
class Permit:
    key: str                  # saved under it
    tier: int                 # of the reputation of the Earth it takes
    mission: Mission


class Permits:
    """ Those granted so far, for the Earth and the outposts """

    def __init__(self) -> None:
        self.granted: set[str] = set()

    def lacks(self, permit: Permit | None) -> bool:
        return permit is not None and permit.key not in self.granted

    def offered(self, permits: Sequence[Permit],
                tier: int) -> list[Permit]:
        """ Those the reputation reached, not granted yet """
        return [
            permit for permit in permits
            if self.lacks(permit) and permit.tier <= tier
        ]

    def validate(self, permit: Permit, board: Board, *holds: Hold) -> None:
        """ Takes the ore from the holds, the first ones first, pays and
        makes the reputation of the `board` as any mission """
        mission = permit.mission
        if not self.lacks(permit) or not mission.can_validate(*holds):
            return
        for name, units in mission.wanted.items():
            take(name, units, holds)
        board.wallet.earn(mission.reward)
        board.validated += 1
        self.granted.add(permit.key)
