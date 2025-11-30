""" Infinite space, repeating itself around the ship """

from typing import Any

from ...logic.config import WORLD_SIZE
from ...logic.world.space import Vec2, wrap_shift
from ..ship.player import Player
from .solar_system import SolarSystem
from .starfield import StarField


def recenter(player: Player, camera: Any, system: SolarSystem,
             stars: StarField) -> Vec2:
    """ Keep coordinates bounded: when the ship leaves the world square,
    move it, the camera and everything else by a whole world size. Space
    repeats itself, so nothing changes on screen. Returns how much. """
    shift = wrap_shift(player.anchor, (WORLD_SIZE / 2, WORLD_SIZE / 2))
    if shift == (0, 0):
        return shift

    player.shift(shift)
    camera_pos = camera.camera_pos
    camera_pos[0] -= shift[0]
    camera_pos[1] -= shift[1]
    system.shift(shift)
    # WORLD_SIZE is a multiple of STAR_TILE, the star field stays the same
    stars.shift(shift)
    return shift


def wrap_space(player: Player, system: SolarSystem,
               stars: StarField) -> None:
    """ Anything farther than half a period from the ship moves to its copy
    on the ship's side. This always happens far off screen, so it can't be
    seen. """
    shift = wrap_shift(system.sun.pos, player.anchor)
    if shift != (0, 0):
        system.shift(shift)
    stars.wrap(player.anchor)
    player.canisters.wrap(player.anchor)
