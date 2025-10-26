""" Background stars, repeated on a tile around the ship """

from collections.abc import Iterable
from dataclasses import dataclass
from random import uniform
from typing import Any

from ...logic.config import STAR_COUNT, STAR_SIZE, STAR_TILE, STAR_WRAP_BATCH
from ...logic.world.space import Vec2, wrap_shift
from ..entities import GameWorld, create_star_entity


@dataclass(slots=True)
class Star:
    # KivEnt position component, kept since looking entities up is too slow
    # to move thousands of stars at once
    position: Any
    pos: Vec2

    def shift(self, shift: Vec2) -> None:
        self.pos = (self.pos[0] + shift[0], self.pos[1] + shift[1])
        self.position.x, self.position.y = self.pos


class StarField:

    def __init__(self, gameworld: GameWorld) -> None:
        self.stars: list[Star] = []
        for _ in range(STAR_COUNT):
            pos = (uniform(0, STAR_TILE), uniform(0, STAR_TILE))
            position = create_star_entity(gameworld, pos, uniform(*STAR_SIZE))
            self.stars.append(Star(position, pos))
        self.cursor = 0

    def wrap(self, center: Vec2) -> None:
        """ Check a batch of stars on each frame: they all get checked every
        few frames, long before they come on screen """
        start = self.cursor
        self.wrap_stars(self.stars[start:start + STAR_WRAP_BATCH], center)
        self.cursor = (start + STAR_WRAP_BATCH) % len(self.stars)

    def wrap_all(self, center: Vec2) -> None:
        self.wrap_stars(self.stars, center)

    def wrap_stars(self, stars: Iterable[Star], center: Vec2) -> None:
        """ Move stars to their copy closest to center """
        for star in stars:
            shift = wrap_shift(star.pos, center, STAR_TILE)
            if shift != (0, 0):
                star.shift(shift)

    def shift(self, shift: Vec2) -> None:
        for star in self.stars:
            star.shift(shift)
