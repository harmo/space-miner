""" Recolor the asteroid images, one per mineral and shape, and fill the
parts their drawing encloses, which are transparent. From
assets/images/asteroids/ to assets/images/asteroids/minerals/. Draws the
canisters of each mineral too. The planets are painted, see
draw_planets.py and draw_earth.py.

    uv run python -m tools.recolor
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from app.logic.mining.canisters import canister_texture
from app.logic.mining.minerals import (
    ASTEROID_SHAPES,
    MINERALS,
    asteroid_texture,
)

from .canister_art import add_glow, draw_canister
from .masks import holes_mask
from .paint import Color, hex_color

IMAGES = Path(__file__).parent.parent / 'assets' / 'images'
ASTEROIDS_DIR = IMAGES / 'asteroids'
MINERALS_DIR = ASTEROIDS_DIR / 'minerals'
CANISTERS_DIR = IMAGES / 'canisters'

@dataclass(frozen=True)
class Palette:
    lines: Color
    fill: Color


def layer(
    size: tuple[int, int],
    color: Color,
    mask: Image.Image
) -> Image.Image:
    image = Image.new('RGBA', size, (*color, 0))
    image.putalpha(mask)
    return image


def recolor(original: Image.Image, palette: Palette) -> Image.Image:
    size = original.size
    alpha = original.getchannel('A')
    box = alpha.getbbox()
    if box is None:
        raise ValueError('empty image')

    result = layer(size, palette.fill, holes_mask(alpha))

    result.alpha_composite(layer(size, palette.lines, alpha))
    return result


def main() -> None:
    MINERALS_DIR.mkdir(exist_ok=True)
    for mineral_name, mineral in MINERALS.items():
        palette = Palette(hex_color(mineral.lines), hex_color(mineral.fill))
        for shape in ASTEROID_SHAPES:
            original = Image.open(
                ASTEROIDS_DIR / f'asteroid{shape}.png'
            ).convert('RGBA')
            name = asteroid_texture(mineral_name, shape)
            image = recolor(original, palette)
            if mineral.glow:
                image = add_glow(image, hex_color(mineral.fill))
            image.save(MINERALS_DIR / f'{name}.png')
            print(f'minerals/{name}.png')

        CANISTERS_DIR.mkdir(exist_ok=True)
        canister = draw_canister(
            hex_color(mineral.lines), hex_color(mineral.fill)
        )
        if mineral.glow:
            canister = add_glow(canister, hex_color(mineral.fill))
        name = canister_texture(mineral_name)
        canister.save(CANISTERS_DIR / f'{name}.png')
        print(f'canisters/{name}.png')


if __name__ == '__main__':
    main()
