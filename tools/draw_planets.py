""" Draw the planets other than the Earth, each in its own character: gas
giants in bands, a rocky world, an ice giant, a cloudy one, a ringed one,
the Moon, and Cérès, a dwarf world in the belt around the sun.
Shaded towards their edge like the Earth, see draw_earth.py.

    uv run python -m tools.draw_planets
"""

import math
from collections.abc import Callable, Sequence
from pathlib import Path
from random import Random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from app.logic.base.config import PAD_DIRECTION
from app.logic.config import PLANET_IMAGE_SCALE

from .masks import dented_mask, disc_mask
from .paint import (
    SIZE,
    Color,
    color_map,
    latitude,
    layer,
    lut,
    octaves,
    shade,
    winds,
)
from .planet_styles import STYLES, Storm, Style

PLANETS_DIR = Path(__file__).parent.parent / 'assets' / 'images' / 'planets'


def spherical(values: Image.Image) -> Image.Image:
    """ Bands of latitude seen on a sphere: narrower towards the poles """
    return values.point(lut(
        lambda v: (math.asin(max(-1., min(1., 2 * v - 1))) / math.pi + .5)
    ))


def bands(rng: Random, style: Style) -> Image.Image:
    rows = spherical(Image.linear_gradient('L').resize((SIZE, SIZE)))
    # Waving slowly along the bands, finer eddies over them
    flow = Image.blend(winds(rng, 4, 14), winds(rng, 12, 40), .35)
    waves = Image.blend(rows, flow, style.swirl)
    return color_map(waves, style.stops, style.bands).convert('RGBA')


def terrain(rng: Random, style: Style) -> Image.Image:
    ground = octaves(rng, 5, 14, 36)
    image = color_map(ground, style.stops).convert('RGBA')
    seas = style.seas
    plains = octaves(rng, 5, 14).point(lut(lambda v: (v - .55) * 3 * seas))
    image.alpha_composite(layer(style.sea or style.stops[0], plains))
    return image


def storm(image: Image.Image, radius: float, spot: Storm) -> None:
    (x, y), (width, height) = spot.at, spot.size
    center = SIZE / 2 + x * radius, SIZE / 2 + y * radius
    half = width * radius / 2, height * radius / 2
    oval = Image.new('L', (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(oval)
    draw.ellipse(
        (center[0] - half[0], center[1] - half[1],
         center[0] + half[0], center[1] + half[1]), fill=210,
    )
    image.alpha_composite(layer(
        spot.color, oval.filter(ImageFilter.GaussianBlur(radius * .03))
    ))
    # A lighter eye
    eye = Image.new('L', (SIZE, SIZE), 0)
    ImageDraw.Draw(eye).ellipse(
        (center[0] - half[0] * .45, center[1] - half[1] * .4,
         center[0] + half[0] * .45, center[1] + half[1] * .4), fill=90,
    )
    image.alpha_composite(layer(
        (255, 255, 255), eye.filter(ImageFilter.GaussianBlur(radius * .03))
    ))


def streaks(rng: Random, image: Image.Image, amount: float) -> None:
    """ Light clouds drawn out along the bands """
    wisps = Image.blend(winds(rng, 5, 30), winds(rng, 14, 70), .4)
    image.alpha_composite(layer((255, 255, 255), wisps.point(
        lut(lambda v: (v - .6) * 3.5 * amount)
    )))


def square(x: float, y: float, half: float) -> tuple[float, ...]:
    """ Around a center """
    return x - half, y - half, x + half, y + half


def craters(
    rng: Random,
    image: Image.Image,
    count: int,
    radius: float,
    shadow: Color
) -> None:
    dark = Image.new('L', (SIZE, SIZE), 0)
    light = Image.new('L', (SIZE, SIZE), 0)
    for _ in range(count):
        angle = rng.uniform(0, 2 * math.pi)
        distance = math.sqrt(rng.random()) * radius * .8
        x = SIZE / 2 + math.cos(angle) * distance
        y = SIZE / 2 + math.sin(angle) * distance
        size = rng.uniform(.03, .09) * radius
        # Lit from the upper left: shadowed inside towards it, its rim
        # bright on the other side
        ImageDraw.Draw(dark).ellipse(
            square(x - size * .12, y - size * .12, size * .9), fill=80,
        )
        ImageDraw.Draw(light).ellipse(
            square(x + size * .1, y + size * .1, size),
            outline=70, width=max(2, round(size / 5)),
        )
    blur = ImageFilter.GaussianBlur(2.5)
    image.alpha_composite(layer(shadow, dark.filter(blur)))
    image.alpha_composite(layer((255, 230, 210), light.filter(blur)))


def caps(rng: Random, image: Image.Image) -> None:
    ice = Image.blend(latitude(), octaves(rng, 12, 32), .2).point(
        lut(lambda v: (v - .87) * 12)
    )
    image.alpha_composite(layer((236, 226, 220), ice))


def ring(
    image: Image.Image,
    stops: Sequence[Color],
    radius: float,
    behind: bool
) -> None:
    """ Ellipses around the planet, tilted: the part behind it, or the one
    in front """
    rings = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    outer = SIZE * .49
    # Wider than the planet inside
    width = 1 - radius * 1.2 / outer
    for index in range(40):
        a = outer * (1 - index / 40 * width)
        b = a * .3
        color = stops[index * len(stops) // 40]
        alpha = 0 if index in (8, 9, 22) else 150 + (index % 3) * 25
        band = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
        ImageDraw.Draw(band).ellipse(
            (SIZE / 2 - a, SIZE / 2 - b, SIZE / 2 + a, SIZE / 2 + b),
            outline=(*color, alpha),
            width=max(2, round(outer * width / 40) + 1),
        )
        rings.alpha_composite(band)
    # The upper half goes behind the planet
    half = Image.new('L', (SIZE, SIZE), 0)
    ImageDraw.Draw(half).rectangle(
        (0, 0, SIZE, SIZE / 2) if behind else (0, SIZE / 2, SIZE, SIZE),
        fill=255,
    )
    rings.putalpha(ImageChops.multiply(rings.getchannel('A'), half))
    image.alpha_composite(rings.rotate(25, Image.Resampling.BICUBIC))


def draw_body(rng: Random, style: Style) -> Image.Image:
    """ Filling the image """
    radius = SIZE / 2
    paint: Callable[[Random, Style], Image.Image] = (
        terrain if style.rocky else bands
    )
    body = paint(rng, style)
    for spot in style.storms:
        storm(body, radius, spot)
    if style.streaks:
        streaks(rng, body, style.streaks)
    if style.craters:
        craters(rng, body, style.craters, radius, style.shadow)
    if style.caps:
        caps(rng, body)
    shade(body, radius, style.air, style.glow)
    if style.dents:
        # Round where outposts are built, their pad on top
        mask = dented_mask(rng, SIZE, style.dents, PAD_DIRECTION, 40)
        edged(body, mask)
        body.putalpha(mask)
    else:
        body.putalpha(disc_mask((SIZE, SIZE), (0, 0, SIZE, SIZE), 1))
    return body


def edged(body: Image.Image, mask: Image.Image) -> None:
    """ Darker towards the edge of `mask`, wherever it lies, for the body to
    look round where it was dented """
    inside = mask.filter(ImageFilter.GaussianBlur(SIZE * .04))
    body.alpha_composite(layer((0, 0, 0), ImageChops.multiply(
        mask, inside.point(lut(lambda v: .6 * (1 - v) ** 1.5)),
    )))


def draw_planet(rng: Random, name: str, style: Style) -> Image.Image:
    """ The body smaller in the middle of rings, which the image holds """
    body = draw_body(rng, style)
    if not style.ring:
        return body
    disc = round(SIZE / PLANET_IMAGE_SCALE[name])
    image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    ring(image, style.ring, disc / 2, behind=True)
    image.alpha_composite(
        body.resize((disc, disc), Image.Resampling.LANCZOS),
        ((SIZE - disc) // 2, (SIZE - disc) // 2),
    )
    ring(image, style.ring, disc / 2, behind=False)
    return image


def main() -> None:
    for index, (name, style) in enumerate(STYLES.items()):
        image = draw_planet(Random(index), name, style)
        image.save(PLANETS_DIR / f'{name}.png')
        print(f'planets/{name}.png')


if __name__ == '__main__':
    main()
