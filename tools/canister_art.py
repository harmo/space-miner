""" Drawing of the canisters, and the halo of glowing minerals """

from PIL import Image, ImageDraw, ImageFilter

from app.logic.mining.minerals import GLOW_SCALE

from .masks import SUPERSAMPLING

CANISTER_IMAGE = (96, 48)

Color = tuple[int, int, int]


def add_glow(image: Image.Image, color: Color) -> Image.Image:
    """ Bigger image by GLOW_SCALE, with a soft halo of `color` around
    the drawing """
    width, height = image.size
    size = round(width * GLOW_SCALE), round(height * GLOW_SCALE)
    offset = (size[0] - width) // 2, (size[1] - height) // 2
    alpha = Image.new('L', size, 0)
    alpha.paste(image.getchannel('A'), offset)
    halo = alpha.filter(ImageFilter.GaussianBlur(width * .08))
    glowing = Image.new('RGBA', size, (*color, 0))
    glowing.putalpha(halo.point(lambda a: int(a * .85)))
    glowing.alpha_composite(image, offset)
    return glowing


def draw_canister(lines: Color, fill: Color) -> Image.Image:
    """ Seen from the side: a body with rounded ends, two rings and a
    highlight """
    width, height = CANISTER_IMAGE
    s = SUPERSAMPLING
    big = Image.new('RGBA', (width * s, height * s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    margin = 3 * s
    draw.rounded_rectangle(
        (margin, margin, width * s - margin, height * s - margin),
        radius=(height - 6) * s // 3, fill=(*fill, 255),
        outline=(*lines, 255), width=4 * s,
    )
    for ring in (.26, .74):
        x = width * s * ring
        draw.rectangle(
            (x - 3 * s, margin, x + 3 * s, height * s - margin),
            fill=(*lines, 255),
        )
    # Drawn on its own layer: drawing a translucent color directly would
    # replace the pixels below instead of blending with them
    highlight = Image.new('RGBA', big.size, (0, 0, 0, 0))
    ImageDraw.Draw(highlight).rounded_rectangle(
        (width * s * .32, height * s * .24, width * s * .68,
         height * s * .36),
        radius=2 * s, fill=(255, 255, 255, 90),
    )
    big.alpha_composite(highlight)
    return big.resize((width, height), Image.Resampling.LANCZOS)
