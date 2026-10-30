""" Outposts, built where their site lies by delivering ore from the cargo
of ships landed there, stage after stage. Each stage built offers more to
the ships landing there: fuel, a depot, then a market and missions. """

from dataclasses import dataclass, replace
from typing import Literal

from ..mining.ore import whole_units
from ..save import Progress
from .post import Services

Form = Literal['ground', 'orbit']    # landed on, or docked to


@dataclass(frozen=True)
class Stage:
    """ A step of building an outpost """
    name: str                 # shown
    materials: tuple[tuple[str, int], ...]  # units to deliver, by mineral
    services: Services        # offered once built, those before included


@dataclass(frozen=True)
class Site:
    """ Where an outpost is built, and how """
    name: str                 # shown
    form: Form
    stages: tuple[Stage, ...]


FUEL = Services(fuel=True)
DEPOT = replace(FUEL, depot=True)
TRADE = replace(DEPOT, market=True, missions=True)

# On the farthest planet from the sun
FRONTIER = Site('Base Frontière', 'ground', (
    Stage('Fondations', (('rock', 120),), FUEL),
    Stage('Habitat', (('rock', 160), ('iron', 40)), DEPOT),
    Stage('Comptoir', (('rock', 200), ('iron', 60), ('copper', 30)), TRADE),
))


class Construction:
    """ An outpost on its site: the stages built, and what was delivered
    for the next one """

    def __init__(self, site: Site) -> None:
        self.site = site
        self.built = 0                      # stages
        self.delivered: dict[str, int] = {}  # for the next stage

    @property
    def progress(self) -> Progress:
        return Progress(self.built, dict(self.delivered))

    def restore(self, progress: Progress) -> None:
        self.built = min(progress.built, len(self.site.stages))
        self.delivered = dict(progress.delivered)

    @property
    def stage(self) -> Stage | None:
        """ Being built, None once all are """
        stages = self.site.stages
        return stages[self.built] if self.built < len(stages) else None

    @property
    def services(self) -> Services:
        """ Of the last stage built, nothing before the first """
        if self.built == 0:
            return Services()
        return self.site.stages[self.built - 1].services

    @property
    def needed(self) -> dict[str, int]:
        """ Units still to deliver for the stage being built, by mineral """
        if self.stage is None:
            return {}
        lacking = {
            name: units - self.delivered.get(name, 0)
            for name, units in self.stage.materials
        }
        return {name: units for name, units in lacking.items() if units > 0}

    def deliver(self, cargo: dict[str, float]) -> Stage | None:
        """ Takes from `cargo` whole units of what is needed. Returns the
        stage built by it, if so. """
        for name, units in self.needed.items():
            taken = min(units, whole_units(cargo.get(name, 0.)))
            if taken <= 0:
                continue
            cargo[name] -= taken
            if cargo[name] <= 1e-6:
                del cargo[name]
            self.delivered[name] = self.delivered.get(name, 0) + taken
        stage = self.stage
        if stage is None or self.needed:
            return None
        self.built += 1
        self.delivered = {}
        return stage
