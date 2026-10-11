""" The far sky, behind everything: nebulae and distant stars sliding slower
than the stars around the ship, reddened near the sun """

from typing import Any

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ...logic.config import HEAT_COLOR, IMAGES, SKY_LAYERS
from ...logic.sky import tile_coords
from ...logic.world.space import Vec2


class SkyLayer:

    def __init__(self, name: str, depth: float, texel: float) -> None:
        texture = CoreImage(f'{IMAGES}/sky/{name}.png').texture
        texture.wrap = 'repeat'
        self.rectangle = Rectangle(texture=texture)
        self.depth = depth
        self.tile = texture.width * dp(texel)


class Sky:

    def __init__(self, canvas: Any) -> None:
        # Moved along with the world, so it doesn't jump when the world does
        self.origin: Vec2 = (0., 0.)
        with canvas:
            Color(1., 1., 1., 1.)
            self.layers = [SkyLayer(*layer) for layer in SKY_LAYERS]
            self.veil_color = Color(*HEAT_COLOR, 0.)
            self.veil = Rectangle()
            # The game is drawn over it in its own colors
            Color(1., 1., 1., 1.)

    def draw(self, pos: Vec2, size: Vec2, camera: Any, heat: float) -> None:
        """ Around the camera, `heat` from 0 to 1 """
        center_x, center_y = camera.get_camera_center()
        scale = camera.camera_scale
        travel = (
            (center_x - self.origin[0]) / scale,
            (center_y - self.origin[1]) / scale,
        )
        for layer in self.layers:
            layer.rectangle.pos = pos
            layer.rectangle.size = size
            layer.rectangle.tex_coords = tile_coords(
                travel, layer.depth, size, layer.tile
            )
        self.veil.pos = pos
        self.veil.size = size
        self.veil_color.a = heat

    def shift(self, shift: Vec2) -> None:
        self.origin = (self.origin[0] + shift[0], self.origin[1] + shift[1])
