""" Draw the Earth from the continents of its original icon: smooth coasts,
muted colors, shallow seas, deserts, ice caps, a few clouds, shaded
towards its edge. Also writes where the ground is, which the ship lands
on.

    uv run python -m tools.draw_earth
"""

from pathlib import Path
from random import Random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .masks import disc_mask, touching_rim
from .paint import SIZE, latitude, layer, lut, octaves, shade

PLANETS_DIR = Path(__file__).parent.parent / 'assets' / 'images' / 'planets'
ORIGINAL = PLANETS_DIR / 'original' / 'earth.png'
RIM = .1                      # outline of the icon, in planet radii
SEED = 3                      # the same Earth on every run

OCEAN = (28, 74, 116)
SHALLOW = (46, 108, 146)
LAND = (92, 128, 80)
FOREST = (64, 100, 60)
DESERT = (156, 138, 94)
ICE = (226, 233, 237)
AIR = (150, 200, 236)


def continents(rng: Random) -> Image.Image:
    """ Land of the icon, up to the edge where it reached the outline,
    with smooth and slightly ragged coasts """
    original = Image.open(ORIGINAL).convert('RGBA').getchannel('A')
    box = original.getbbox()
    assert box is not None
    center = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    radius = min(box[2] - box[0], box[3] - box[1]) / 2
    inner = radius * (1 - RIM)
    reaching = touching_rim(original, center, inner)

    scale = SIZE / original.width
    land = original.resize((SIZE, SIZE), Image.Resampling.BICUBIC)
    whole = (0, 0, SIZE, SIZE)
    land = ImageChops.multiply(
        land, disc_mask((SIZE, SIZE), whole, (radius - inner + 2) * scale)
    )
    # Out to the edge where the continents reached the outline
    edges = Image.new('L', (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(edges)
    for step, touching in enumerate(reaching):
        if touching:
            # Pillow turns clockwise, rows going down
            start = -(step + 1) / 10
            draw.pieslice(whole, start, start + .1, fill=255)
    rim = ImageChops.subtract(
        disc_mask((SIZE, SIZE), whole, 0),
        disc_mask((SIZE, SIZE), whole, (radius - inner + 6) * scale),
    )
    land = ImageChops.lighter(land, ImageChops.multiply(edges, rim))

    coasts = land.filter(ImageFilter.GaussianBlur(7))
    ragged = Image.blend(coasts, octaves(rng, 24, 64), .3)
    return ragged.point(lut(lambda v: (v - .48) * 12)).filter(
        ImageFilter.GaussianBlur(1.2)
    )


def draw_earth(rng: Random) -> tuple[Image.Image, Image.Image]:
    """ The Earth, and where its ground is """
    land = continents(rng)
    disc = disc_mask((SIZE, SIZE), (0, 0, SIZE, SIZE), 1)
    poles = latitude()

    earth = Image.new('RGBA', (SIZE, SIZE), (*OCEAN, 255))
    shallow = land.filter(ImageFilter.GaussianBlur(22))
    earth.alpha_composite(layer(SHALLOW, shallow.point(lut(
        lambda v: v * 1.6 * .7
    ))))
    earth.alpha_composite(layer(LAND, land))
    forests = octaves(rng, 10, 28).point(lut(lambda v: (v - .5) * 2 * .7))
    earth.alpha_composite(layer(FOREST, ImageChops.multiply(land, forests)))
    # Deserts around the tropics
    tropics = poles.point(lut(lambda v: 1 - abs(v - .3) * 6))
    sand = ImageChops.multiply(tropics, octaves(rng, 8, 24).point(
        lut(lambda v: (v - .45) * 2.5 * .8)
    ))
    earth.alpha_composite(layer(DESERT, ImageChops.multiply(land, sand)))
    ice = Image.blend(poles, octaves(rng, 16, 40), .15).point(
        lut(lambda v: (v - .84) * 14)
    )
    earth.alpha_composite(layer(ICE, ice))
    # Thin and sparse
    clouds = octaves(rng, 7, 18, 40).filter(ImageFilter.GaussianBlur(6))
    clouds = clouds.point(lut(lambda v: (v - .6) * 3 * .35))
    earth.alpha_composite(layer((255, 255, 255), clouds))
    shade(earth, SIZE / 2, AIR)
    earth.putalpha(disc)

    ground = layer((255, 255, 255), ImageChops.multiply(land, disc))
    return earth, ground


def main() -> None:
    earth, ground = draw_earth(Random(SEED))
    earth.save(PLANETS_DIR / 'earth.png')
    ground.save(PLANETS_DIR / 'earth_ground.png')
    print('planets/earth.png, planets/earth_ground.png')


if __name__ == '__main__':
    main()
