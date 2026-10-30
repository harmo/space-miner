""" Textures of the ships, put together from the images of their hull and
parts, once per design """

import math

from kivent_core.managers.resource_managers import texture_manager
from kivy.core.image import Image as CoreImage
from kivy.graphics import ClearBuffers, ClearColor, Color, Fbo, Rectangle
from kivy.graphics.texture import Texture

from ...logic.config import IMAGES
from ...logic.ship.shipyard import (
    SHIP_PIXELS,
    Design,
    design_key,
    pieces,
    tint,
)

# By texture name, kept along with their textures
made: dict[str, Fbo] = {}


def piece_texture(image: str) -> Texture:
    texture: Texture = CoreImage(f'{IMAGES}/ships/{image}.png').texture
    return texture


def compose(design: Design, size: tuple[float, float]) -> Fbo:
    """ Kivy blends alpha by adding it up, which suits drawing on a
    transparent background """
    length, width = size
    fbo = Fbo(size=(
        math.ceil(length * SHIP_PIXELS), math.ceil(width * SHIP_PIXELS)
    ))
    with fbo:
        ClearColor(0, 0, 0, 0)
        ClearBuffers()
        Color(*tint(design), 1)
        for image, (x, y, w, h) in pieces(design):
            Rectangle(
                texture=piece_texture(image),
                pos=(
                    (x + length / 2) * SHIP_PIXELS,
                    (y + width / 2) * SHIP_PIXELS,
                ),
                size=(w * SHIP_PIXELS, h * SHIP_PIXELS),
            )
    fbo.draw()
    return fbo


def ship_texture(design: Design, size: tuple[float, float]) -> str:
    """ Name of the texture of the ship, made the first time """
    name = f'ship {design_key(design)}'
    if name not in made:
        made[name] = compose(design, size)
        texture_manager.load_texture(name, made[name].texture)
    return name


def ship_preview(design: Design, size: tuple[float, float]) -> Texture:
    """ Texture of the ship, for the interface """
    texture: Texture = made[ship_texture(design, size)].texture
    return texture
