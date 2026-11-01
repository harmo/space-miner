""" How docks and their shuttles look: a pad on the surface, or on the ring
of a station, between two lit pylons, and a stubby amber barge, nothing like
the ship, its shuttle standing there or flying its way """

import math
from collections.abc import Iterable

from ...logic.base.quays import Quay, shuttle_position
from ...logic.colors import Rgb
from ...logic.config import SHUTTLE_COLOR
from ...logic.world.space import Vec2
from .outpost_look import DARK, GLASS, SEEN, STEEL, Frame, blinking
from .overlay import Overlay

HOLD = (.55, .4, .16)
FLAME = (.5, .85, 1.)
PAD = 30.                     # pixels, half its width
PYLON = 22.                   # pixels high

Part = tuple[Iterable[Vec2], Rgb, Rgb | None]

# Along its nose, then across it, in pixels
PARTS: tuple[Part, ...] = (
    (((-14., -8.), (-9., -8.), (-9., -3.), (-14., -3.)), STEEL, DARK),
    (((-14., 3.), (-9., 3.), (-9., 8.), (-14., 8.)), STEEL, DARK),
    (((-11., -6.), (6., -6.), (12., -2.5), (12., 2.5), (6., 6.), (-11., 6.)),
     SHUTTLE_COLOR, DARK),
    (((-8., -6.), (-3., -6.), (-3., 6.), (-8., 6.)), HOLD, None),
    (((-1., -6.), (4., -6.), (4., 6.), (-1., 6.)), HOLD, None),
    (((7., -3.), (11., -1.5), (11., 1.5), (7., 3.)), GLASS, DARK),
)


def in_place(point: Vec2, pos: Vec2, heading: float) -> Vec2:
    along, across = point
    cos, sin = math.cos(heading), math.sin(heading)
    return (
        pos[0] + along * cos - across * sin,
        pos[1] + along * sin + across * cos,
    )


def draw_shuttle(
    overlay: Overlay,
    pos: Vec2,
    heading: float,
    flying: bool
) -> None:
    if flying:
        for across in (-5.5, 5.5):
            overlay.light(in_place((-17., across), pos, heading), FLAME, .8)
    for points, color, outline in PARTS:
        overlay.shape(
            [in_place(point, pos, heading) for point in points],
            color, outline,
        )


def draw_dock(overlay: Overlay, quay: Quay) -> None:
    frame = Frame(quay.body, quay.direction)
    overlay.band(*frame.box(-PAD, PAD, 4), STEEL, DARK)
    for side, phase in ((-1, .25), (1, .75)):
        along = side * PAD
        overlay.band(*frame.box(along - 2, along + 2, PYLON), STEEL, DARK)
        overlay.light(frame.at(along, PYLON + 2), SHUTTLE_COLOR,
                      blinking(phase))


def draw_quay(overlay: Overlay, quay: Quay, sun: Vec2) -> None:
    """ Its dock if close enough, as for its shuttle wherever it flies """
    center = overlay.camera.get_camera_center()
    shuttle = quay.post.shuttle
    if math.dist(center, quay.spot) < SEEN:
        draw_dock(overlay, quay)
    flying = shuttle_position(quay, sun)
    pos = quay.spot if flying is None else flying
    heading = quay.direction if flying is None else shuttle.heading
    if math.dist(center, pos) < SEEN:
        draw_shuttle(overlay, pos, heading, flying is not None)
