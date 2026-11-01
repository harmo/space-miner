""" The places where games are saved, side by side, each with its solar
system, and what the home page tells of them """

from dataclasses import dataclass

from .save import Save


@dataclass(frozen=True)
class SlotSummary:
    credits: int
    missions: int             # validated, everywhere
    outposts: int             # with something built


def summary(save: Save) -> SlotSummary:
    progress = save.outposts.values()
    return SlotSummary(
        save.credits,
        save.contracts.validated + sum(
            outpost.contracts.validated for outpost in progress
        ),
        sum(outpost.built > 0 for outpost in progress),
    )
