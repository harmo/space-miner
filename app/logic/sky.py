""" The far sky behind the stars: images repeated all over it, which slide
slower than the stars as the ship moves, the slower the farther """

from .world.space import Vec2

TexCoords = tuple[float, float, float, float, float, float, float, float]


def tile_coords(travel: Vec2, depth: float, size: Vec2,
                tile: float) -> TexCoords:
    """ Texture coordinates of a screen of `size` pixels over an image
    repeated every `tile` pixels, slid `depth` times as far as the ship
    has travelled, in pixels too. Counterclockwise from the bottom left
    corner. """
    left = (travel[0] * depth - size[0] / 2) / tile % 1.
    bottom = (travel[1] * depth - size[1] / 2) / tile % 1.
    right = left + size[0] / tile
    top = bottom + size[1] / tile
    return left, bottom, right, bottom, right, top, left, top
