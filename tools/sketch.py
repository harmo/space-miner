""" Drawing tools for the ships: shapes in pixels of the world, from the top
left corner of the image, smoothed by supersampling """

from collections.abc import Callable, Sequence

from PIL import Image, ImageDraw

from app.logic.ship.shipyard import SHIP_PIXELS

SUPERSAMPLING = 4
SCALE = SHIP_PIXELS * SUPERSAMPLING
OUTLINE = .5

Color = tuple[int, int, int]
Point = tuple[float, float]


def hex_color(value: str) -> Color:
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


METAL = hex_color('#c3ccd6')
METAL_DARK = hex_color('#7d8a99')
LINES = hex_color('#2e3844')
ACCENT = hex_color('#e0a33f')
GLASS = hex_color('#5fd0f2')
EMITTER = hex_color('#ff5a4a')
FLAME = hex_color('#ffb347')
ION = hex_color('#7fd8ff')
QUANTUM = hex_color('#c78bff')
STELLAR = hex_color('#ffa23a')
SOLAR = hex_color('#3b6fd1')
FUSION = hex_color('#9fe8ff')
WHITE_HOT = hex_color('#fff3c4')
NOZZLE = hex_color('#1c2128')
PORT = hex_color('#ff4d4d')           # lights, red on the left side
STARBOARD = hex_color('#4dff88')      # and green on the right one


class Sketch:
    """ Shapes drawn in world pixels on a supersampled image """

    def __init__(self, size: tuple[float, float]) -> None:
        self.size = size
        self.image = Image.new(
            'RGBA', (round(size[0] * SCALE), round(size[1] * SCALE)),
            (0, 0, 0, 0),
        )
        self.draw = ImageDraw.Draw(self.image)

    def points(self, points: Sequence[Point]) -> list[Point]:
        return [(x * SCALE, y * SCALE) for x, y in points]

    def polygon(self, points: Sequence[Point], fill: Color,
                outline: bool = True) -> None:
        self.draw.polygon(
            self.points(points), fill=(*fill, 255),
            outline=(*LINES, 255) if outline else None,
            width=round(OUTLINE * SCALE),
        )

    def box(self, left: float, top: float, right: float, bottom: float,
            fill: Color, radius: float = 0., outline: bool = True) -> None:
        self.draw.rounded_rectangle(
            self.points([(left, top), (right, bottom)]),
            radius=radius * SCALE, fill=(*fill, 255),
            outline=(*LINES, 255) if outline else None,
            width=round(OUTLINE * SCALE),
        )

    def oval(self, left: float, top: float, right: float, bottom: float,
             fill: Color, outline: bool = True) -> None:
        self.draw.ellipse(
            self.points([(left, top), (right, bottom)]), fill=(*fill, 255),
            outline=(*LINES, 255) if outline else None,
            width=round(OUTLINE * SCALE),
        )

    def line(self, points: Sequence[Point], color: Color,
             width: float = OUTLINE) -> None:
        self.draw.line(
            self.points(points), fill=(*color, 255),
            width=round(width * SCALE),
        )

    def glint(self, left: float, top: float, right: float,
              bottom: float) -> None:
        """ Translucent white highlight, drawn on its own layer to blend
        with what is below """
        layer = Image.new('RGBA', self.image.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(
            self.points([(left, top), (right, bottom)]),
            fill=(255, 255, 255, 150),
        )
        self.image.alpha_composite(layer)

    def result(self) -> Image.Image:
        width, height = self.size
        return self.image.resize(
            (round(width * SHIP_PIXELS), round(height * SHIP_PIXELS)),
            Image.Resampling.LANCZOS,
        )


Drawing = Callable[[Sketch], None]
