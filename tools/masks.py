""" Masks of the drawings: their round silhouette, or dented as an
asteroid's, the holes they enclose, and their outline """

import math
from random import Random

from PIL import Image, ImageDraw

SUPERSAMPLING = 4             # for smooth disc edges


def disc_mask(
    size: tuple[int, int],
    box: tuple[int, int, int, int],
    shrink: float
) -> Image.Image:
    """ Antialiased disc inscribed in box, shrunk by `shrink` pixels """
    left, top, right, bottom = box
    cx, cy = (left + right) / 2, (top + bottom) / 2
    radius = min(right - left, bottom - top) / 2 - shrink
    big = Image.new('L', (size[0] * SUPERSAMPLING, size[1] * SUPERSAMPLING))
    ImageDraw.Draw(big).ellipse(
        [
            (cx - radius) * SUPERSAMPLING, (cy - radius) * SUPERSAMPLING,
            (cx + radius) * SUPERSAMPLING, (cy + radius) * SUPERSAMPLING,
        ],
        fill=255,
    )
    return big.resize(size, Image.Resampling.LANCZOS)


def dented_mask(
    rng: Random,
    size: int,
    depth: float,
    kept: float,
    kept_half: float
) -> Image.Image:
    """ A disc filling a square image, its edge dented inwards by up to
    `depth` of its radius, unevenly, as an asteroid's: never beyond the
    disc, and kept round `kept_half` degrees on both sides of the angle
    `kept`, counterclockwise from the east """
    phases = [(k, rng.uniform(0, 2 * math.pi), rng.uniform(.4, 1.))
              for k in range(2, 7)]

    def wobble(angle: float) -> float:
        return sum(w * math.sin(k * angle + p) for k, p, w in phases)

    angles = [2 * math.pi * i / 720 for i in range(720)]
    raw = [wobble(angle) for angle in angles]
    low, high = min(raw), max(raw)
    radius = size / 2 * SUPERSAMPLING
    points = []
    for angle, value in zip(angles, raw, strict=True):
        away = abs(math.degrees(math.remainder(angle - math.radians(kept),
                                               2 * math.pi)))
        dented = min(1., max(0., (away - kept_half) / 20))
        dent = depth * dented * (value - low) / (high - low)
        r = radius * (1 - dent)
        points.append((radius + r * math.cos(angle),
                       radius - r * math.sin(angle)))
    big = Image.new('L', (size * SUPERSAMPLING, size * SUPERSAMPLING))
    ImageDraw.Draw(big).polygon(points, fill=255)
    return big.resize((size, size), Image.Resampling.LANCZOS)


def holes_mask(alpha: Image.Image) -> Image.Image:
    """ Transparent areas that can't be reached from the image border """
    solid = alpha.point(lambda a: 255 if a > 127 else 0)
    width, height = solid.size
    border = (
        [(x, y) for x in range(width) for y in (0, height - 1)]
        + [(x, y) for y in range(height) for x in (0, width - 1)]
    )
    # A ring can split the outside in several parts, flood each of them
    for point in border:
        if solid.getpixel(point) == 0:
            ImageDraw.floodfill(solid, point, 128)
    return solid.point(lambda v: 255 if v == 0 else 0)


def touching_rim(
    alpha: Image.Image,
    center: tuple[float, float],
    rim_inner: float
) -> list[bool]:
    """ Whether the drawing reaches the inner edge of the outline, for
    each tenth of a degree """
    radius = rim_inner - 3
    touching: list[bool] = []
    for step in range(3600):
        angle = math.radians(step / 10)
        value = alpha.getpixel((
            round(center[0] + math.cos(angle) * radius),
            round(center[1] - math.sin(angle) * radius),
        ))
        assert isinstance(value, int)
        touching.append(value > 127)
    return touching
