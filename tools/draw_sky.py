""" Draw the far sky behind the stars of the game, in two layers that
repeat themselves seamlessly: nebulae along the band of a galaxy, and
distant stars of all colors, a few bright ones glowing.

    uv run python -m tools.draw_sky
"""

import math
from pathlib import Path
from random import Random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .paint import Color, layer, lut

SKY_DIR = Path(__file__).parent.parent / 'assets' / 'images' / 'sky'
SIZE = 1024                   # a power of two, so the image can repeat
SEED = 11

SPACE = (3, 4, 10)
GASES: tuple[tuple[Color, float], ...] = (    # and how much they show
    ((96, 30, 104), .55),     # glowing hydrogen and oxygen
    ((22, 74, 104), .5),
    ((34, 38, 112), .45),
    ((122, 40, 36), .3),
)
STARLIGHT = (150, 136, 118)   # of the stars too far to be seen apart
DUST = (2, 2, 4)
BAND_WIDTH = .16              # of the galaxy, for the image
# Stars from the hottest to the coolest, and how often
STAR_COLORS: tuple[tuple[Color, int], ...] = (
    ((170, 196, 255), 3),
    ((214, 226, 255), 4),
    ((255, 255, 255), 5),
    ((255, 240, 214), 3),
    ((255, 210, 160), 2),
    ((255, 168, 130), 1),
)
FAINT_STARS = 2600
STARS = 320
BRIGHT_STARS = 22
GALAXIES = 3
PADDING = 100                 # around the sky, for the galaxies on its edge


def periodic(image: Image.Image, blur: float) -> Image.Image:
    """ Blurred as if it repeated itself all around """
    width, height = image.size
    tiles = Image.new(image.mode, (width * 3, height * 3))
    for x in range(3):
        for y in range(3):
            tiles.paste(image, (x * width, y * height))
    blurred = tiles.filter(ImageFilter.GaussianBlur(blur))
    return blurred.crop((width, height, width * 2, height * 2))


def tiled_noise(rng: Random, cells: int) -> Image.Image:
    """ Smooth random values, `cells` across the image, which repeats
    itself seamlessly """
    small = Image.new('L', (cells, cells))
    small.putdata([rng.randrange(256) for _ in range(cells * cells)])
    tiles = Image.new('L', (cells * 3, cells * 3))
    for x in range(3):
        for y in range(3):
            tiles.paste(small, (x * cells, y * cells))
    smooth = tiles.resize((SIZE * 3, SIZE * 3), Image.Resampling.BICUBIC)
    middle = smooth.crop((SIZE, SIZE, SIZE * 2, SIZE * 2))
    return periodic(middle, SIZE / cells / 3)


def tiled_octaves(rng: Random, *cells: int) -> Image.Image:
    result = tiled_noise(rng, cells[0])
    for weight, count in enumerate(cells[1:], start=2):
        result = Image.blend(result, tiled_noise(rng, count), 1 / weight)
    return result


def ridges(rng: Random, *cells: int) -> Image.Image:
    """ Thin bright lines where the noise crosses its middle: the
    filaments of the gas """
    return tiled_octaves(rng, *cells).point(
        lut(lambda v: (1 - abs(2 * v - 1)) ** 6)
    )


def band() -> Image.Image:
    """ Across the image diagonally, wrapping around so that it goes on
    from one copy of the image to the next """
    def strength(offset: int) -> int:
        middle = (offset % SIZE) / SIZE - .5
        return round(255 * math.exp(-(middle / BAND_WIDTH) ** 2))
    profile = [strength(offset) for offset in range(SIZE)]
    image = Image.new('L', (SIZE, SIZE))
    image.putdata([profile[(x - y) % SIZE] for y in range(SIZE)
                   for x in range(SIZE)])
    return image


def faded(values: Image.Image, amount: float) -> Image.Image:
    return values.point(lut(lambda v: v * amount))


def draw_nebula(rng: Random) -> Image.Image:
    sky = Image.new('RGBA', (SIZE, SIZE), (*SPACE, 255))
    galaxy = band()
    # Mostly in the band of the galaxy, faint farther from it
    near_band = galaxy.point(lut(lambda v: .3 + .7 * v))
    for color, amount in GASES:
        clouds = tiled_octaves(rng, 3, 6, 12, 24).point(
            lut(lambda v: (v - .5) * 5)
        )
        clouds = ImageChops.multiply(clouds, near_band)
        wisps = ImageChops.multiply(ridges(rng, 4, 9, 20), clouds)
        sky.alpha_composite(layer(color, faded(clouds, amount)))
        sky.alpha_composite(layer(color, faded(wisps, amount * 2)))
    glow = ImageChops.multiply(galaxy, tiled_octaves(rng, 5, 12, 30))
    sky.alpha_composite(layer(STARLIGHT, faded(glow, .5)))
    # Lanes of dust darken the middle of the band
    lanes = ImageChops.multiply(
        galaxy.point(lut(lambda v: v ** 3)), ridges(rng, 3, 7, 16)
    )
    sky.alpha_composite(layer(DUST, faded(lanes, .8)))
    return sky.convert('RGB')


def star_color(rng: Random) -> Color:
    colors, weights = zip(*STAR_COLORS, strict=True)
    color: Color = rng.choices(colors, weights)[0]
    return color


def copies(x: float, y: float, margin: float) -> list[tuple[float, float]]:
    """ Where to draw what is at x, y so that it goes on across the edges
    """
    xs = [x] + [x + shift for shift in (-SIZE, SIZE)
                if -margin < x + shift < SIZE + margin]
    ys = [y] + [y + shift for shift in (-SIZE, SIZE)
                if -margin < y + shift < SIZE + margin]
    return [(a, b) for a in xs for b in ys]


def dots(rng: Random, image: Image.Image, count: int,
         sizes: tuple[float, float], alphas: tuple[int, int]) -> None:
    draw = ImageDraw.Draw(image)
    for _ in range(count):
        x, y = rng.uniform(0, SIZE), rng.uniform(0, SIZE)
        radius = rng.uniform(*sizes)
        color = (*star_color(rng), rng.randint(*alphas))
        for cx, cy in copies(x, y, radius):
            draw.ellipse((cx - radius, cy - radius, cx + radius,
                          cy + radius), fill=color)


def bright_star(rng: Random, glows: Image.Image, cores: Image.Image) -> None:
    x, y = rng.uniform(0, SIZE), rng.uniform(0, SIZE)
    color = star_color(rng)
    halo = rng.uniform(4, 9)
    spikes = rng.random() < .4
    glow, core = ImageDraw.Draw(glows), ImageDraw.Draw(cores)
    for cx, cy in copies(x, y, halo * 4):
        glow.ellipse((cx - halo, cy - halo, cx + halo, cy + halo),
                     fill=(*color, 110))
        if spikes:
            # Light spread by the lens of a telescope, faint and thin
            reach = halo * 3.5
            glow.line((cx - reach, cy, cx + reach, cy), (*color, 90), 1)
            glow.line((cx, cy - reach, cx, cy + reach), (*color, 90), 1)
        core.ellipse((cx - 1.4, cy - 1.4, cx + 1.4, cy + 1.4),
                     fill=(255, 255, 255, 255))


def galaxy(rng: Random, image: Image.Image) -> None:
    """ A faraway spiral, a tilted oval with a bright core. On an image
    wider than the sky by PADDING all around. """
    width = rng.uniform(26, 44)
    flat = Image.new('RGBA', (round(width * 3), round(width * 3)))
    draw = ImageDraw.Draw(flat)
    middle = width * 1.5
    color = star_color(rng)
    for step in range(6):
        a = width / 2 * (1 - step / 6)
        b = a * rng.uniform(.35, .5)
        draw.ellipse((middle - a, middle - b, middle + a, middle + b),
                     fill=(*color, 30 + step * 18))
    turned = flat.rotate(rng.uniform(0, 180), Image.Resampling.BICUBIC)
    soft = turned.filter(ImageFilter.GaussianBlur(width / 10))
    x, y = rng.uniform(0, SIZE), rng.uniform(0, SIZE)
    for cx, cy in copies(x, y, width * 1.5):
        image.alpha_composite(soft, (round(cx - middle) + PADDING,
                                     round(cy - middle) + PADDING))


def draw_stars(rng: Random) -> Image.Image:
    """ On a transparent image, over the nebulae """
    wide = SIZE + 2 * PADDING
    galaxies = Image.new('RGBA', (wide, wide), (0, 0, 0, 0))
    for _ in range(GALAXIES):
        galaxy(rng, galaxies)
    stars = galaxies.crop((PADDING, PADDING, SIZE + PADDING, SIZE + PADDING))
    dots(rng, stars, FAINT_STARS, (.5, .8), (40, 150))
    dots(rng, stars, STARS, (.8, 1.3), (140, 230))
    glows = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    cores = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    for _ in range(BRIGHT_STARS):
        bright_star(rng, glows, cores)
    stars.alpha_composite(periodic(glows, 3.5))
    stars.alpha_composite(periodic(cores, .8))
    return stars


def main() -> None:
    SKY_DIR.mkdir(exist_ok=True)
    rng = Random(SEED)
    draw_nebula(rng).save(SKY_DIR / 'nebula.png')
    draw_stars(rng).save(SKY_DIR / 'far_stars.png')
    print('sky/nebula.png, sky/far_stars.png')


if __name__ == '__main__':
    main()
