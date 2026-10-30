""" Textures loaded from the assets, or generated when there is no image """

import math
from collections.abc import Callable

from kivent_core.managers.resource_managers import texture_manager
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

from ..logic.config import IMAGES, MOON, PLANETS, STATION, SUN_DISC
from ..logic.mining.canisters import canister_texture
from ..logic.mining.minerals import ASTEROID_SHAPES, MINERALS, asteroid_texture
from ..logic.ship.config import GROUND_DEPTH

Rgba = tuple[int, int, int, int]
# (distance from the center, from 0 to 1 at the edge, half size) -> color
Pixel = Callable[[float, float], Rgba]


def make_texture(size: int, pixel: Pixel) -> Texture:
    pixels = bytearray()
    half = size / 2
    for y in range(size):
        for x in range(size):
            distance = math.hypot(x + .5 - half, y + .5 - half) / half
            pixels += bytes(pixel(distance, half))
    texture = Texture.create(size=(size, size), colorfmt='rgba')
    texture.blit_buffer(bytes(pixels), colorfmt='rgba', bufferfmt='ubyte')
    return texture


def star_pixel(distance: float, half: float) -> Rgba:
    """ Soft white dot """
    alpha = 255 * min(1., max(0., 1.5 * (1. - distance)))
    return 255, 255, 255, int(alpha)


def sun_pixel(distance: float, half: float) -> Rgba:
    """ Yellow disc with an orange glow """
    glow = 1. - max(0., distance - SUN_DISC) / (1. - SUN_DISC)
    glow_alpha = 150 * max(0., glow) ** 2
    disc = min(1., max(0., (SUN_DISC - distance) * half + .5))
    return (
        255,
        int(170 + 35 * disc),
        int(50 + 20 * disc),
        int(glow_alpha + (255 - glow_alpha) * disc),
    )


def unseen_pixel(distance: float, half: float) -> Rgba:
    return 0, 0, 0, 0


def load_image(source: str) -> None:
    tex_key = texture_manager.load_image(source)
    # load_image maps images upside down, flip uvs like load_atlas does
    texture_manager.get_uvs(tex_key)[:] = [0., 1., 1., 0.]


def load_textures() -> None:
    for name in ['earth', *PLANETS]:
        load_image(f'{IMAGES}/planets/{name}.png')
    load_image(f'{IMAGES}/planets/{MOON}.png')
    for mineral in MINERALS:
        for shape in ASTEROID_SHAPES:
            name = asteroid_texture(mineral, shape)
            load_image(f'{IMAGES}/asteroids/minerals/{name}.png')
        load_image(f'{IMAGES}/canisters/{canister_texture(mineral)}.png')
    texture_manager.load_texture('star', make_texture(8, star_pixel))
    texture_manager.load_texture('sun', make_texture(256, sun_pixel))
    texture_manager.load_texture(STATION, make_texture(4, unseen_pixel))


def ground_edge(planet: str) -> list[bool]:
    """ Whether there is ground just inside the edge of the planet, one
    sample per degree counterclockwise from the east. Read from the image
    of its ground, drawn along with it. """
    image = CoreImage(
        f'{IMAGES}/planets/{planet}_ground.png', keep_data=True
    )
    width, height = image.size
    radius = min(width, height) / 2 * (1 - GROUND_DEPTH)
    samples = []
    for degrees in range(360):
        angle = math.radians(degrees)
        # Rows of the image go down
        x = width / 2 + math.cos(angle) * radius
        y = height / 2 - math.sin(angle) * radius
        samples.append(image.read_pixel(x, y)[3] > .5)
    return samples


def texture_size(name: str) -> tuple[float, float]:
    width, height = texture_manager.get_size_by_name(name)
    return width, height
