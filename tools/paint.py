""" Painting tools for the Earth and the planets: smooth noise, gradients,
color maps, and the shading that makes a disc look round. Images are
SIZE pixels across, with the disc of the planet in their middle. """

from collections.abc import Callable
from random import Random

from PIL import Image, ImageFilter

SIZE = 1024

Color = tuple[int, int, int]


def hex_color(value: str) -> Color:
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


def layer(color: Color, alpha: Image.Image) -> Image.Image:
    image = Image.new('RGBA', alpha.size, (*color, 0))
    image.putalpha(alpha)
    return image


def noise(rng: Random, cells: int) -> Image.Image:
    """ Smooth random values, `cells` across the image """
    small = Image.new('L', (cells, cells))
    small.putdata([rng.randrange(256) for _ in range(cells * cells)])
    smooth = small.resize((SIZE, SIZE), Image.Resampling.BICUBIC)
    # Rounds off the corners of the cells
    return smooth.filter(ImageFilter.GaussianBlur(SIZE / cells / 3))


def octaves(rng: Random, *cells: int) -> Image.Image:
    """ Coarse noise with finer ones over it """
    result = noise(rng, cells[0])
    for weight, count in enumerate(cells[1:], start=2):
        result = Image.blend(result, noise(rng, count), 1 / weight)
    return result


def lut(function: Callable[[float], float]) -> list[int]:
    """ For Image.point, from a function of 0 to 1 giving 0 to 1 """
    return [round(255 * min(1., max(0., function(v / 255)))) for v in
            range(256)]


def radial(radius: float) -> Image.Image:
    """ Distance to the center, 255 at `radius`, beyond too """
    disc = round(2 * radius)
    gradient = Image.radial_gradient('L').resize(
        (disc, disc), Image.Resampling.BICUBIC
    )
    image = Image.new('L', (SIZE, SIZE), 255)
    image.paste(gradient, ((SIZE - disc) // 2, (SIZE - disc) // 2))
    return image


def latitude() -> Image.Image:
    """ Distance to the equator, 255 at the poles """
    gradient = Image.linear_gradient('L').resize((SIZE, SIZE))
    return gradient.point(lut(lambda v: abs(2 * v - 1)))


def shade(image: Image.Image, radius: float, air: Color,
          glow: float = .55) -> None:
    """ Darker towards the edge of the disc, lit by a thin atmosphere on
    it """
    distance = radial(radius)
    image.alpha_composite(layer((0, 0, 0), distance.point(
        lut(lambda v: .5 * v ** 3)
    )))
    image.alpha_composite(layer(air, distance.point(
        lut(lambda v: (v - .9) * 5 * glow if v < 1 else 0)
    )))
