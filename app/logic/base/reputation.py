""" Reputation, earned by validating missions: higher tiers of parts are
sold to those who proved themselves, and clients order more of them """

from ..ship.hulls import Hull
from ..ship.parts import Part
from .config import TIER_MISSIONS


def tier(validated: int) -> int:
    """ Reached with that many missions validated, from 1 """
    return sum(validated >= needed for needed in TIER_MISSIONS)


def next_tier(validated: int) -> tuple[int, int] | None:
    """ The next tier and the missions it takes, None at the top """
    reached = tier(validated)
    if reached >= len(TIER_MISSIONS):
        return None
    return reached + 1, TIER_MISSIONS[reached]


def is_sold(item: Hull | Part, validated: int) -> bool:
    return item.tier <= tier(validated)
