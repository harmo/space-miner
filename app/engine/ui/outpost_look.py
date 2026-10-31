""" How outposts look as they are built. On the ground, drawn along the
curve of the surface as small bodies are round: a beacon on a bare site,
then a pad, a dome and tanks, towers. In orbit, stations: a floating
beacon, then a ring around a hub with its port, lit, solar panels. """

import math
import time

from ...logic.config import OUTPOST_COLOR
from ...logic.world.space import Vec2
from ..base.outposts import Outpost
from .overlay import Overlay

STEEL = (.42, .47, .54)
DARK = (.16, .18, .22)
GLASS = (.7, .82, .9)
RED = (1., .3, .25)
BLINK = 1.2                   # seconds, of the lights
SEEN = 2000.                  # drawn only this close to the camera
STEP = 8.                     # pixels, between points of long shapes


class Frame:
    """ On the surface, `along` it from the middle of the pad, and `up`
    from it, in pixels """

    def __init__(self, outpost: Outpost) -> None:
        self.center = outpost.body.pos
        self.radius = outpost.body.radius
        self.direction = outpost.direction

    def at(self, along: float, up: float) -> Vec2:
        x, y = self.center
        angle = self.direction + along / self.radius
        distance = self.radius + up
        return (
            x + math.cos(angle) * distance, y + math.sin(angle) * distance,
        )

    def box(self, left: float, right: float, top: float,
            bottom: float = -3.) -> tuple[list[Vec2], list[Vec2]]:
        """ Its lower and upper edges, bending with the surface: sunk a
        little into the ground, not to float above it """
        steps = max(1, math.ceil((right - left) / STEP))
        alongs = [left + (right - left) * k / steps for k in range(steps + 1)]
        return (
            [self.at(along, bottom) for along in alongs],
            [self.at(along, top) for along in alongs],
        )


def blinking(phase: float) -> float:
    """ From faint to bright, `phase` from 0 to 1 along the blink """
    return .3 + .7 * (.5 + .5 * math.cos(
        2 * math.pi * (time.monotonic() / BLINK + phase)
    ))


def draw_outpost(overlay: Overlay, outpost: Outpost) -> None:
    center = overlay.camera.get_camera_center()
    if math.dist(center, outpost.pos) > SEEN + outpost.body.radius:
        return
    if outpost.construction.site.form == 'orbit':
        draw_station(overlay, outpost)
        return
    frame = Frame(outpost)
    built = outpost.construction.built
    half = outpost.construction.site.pad_width / 2
    if built == 0:
        corners(overlay, frame, half)
    else:
        overlay.band(*frame.box(-half, half, 4), STEEL, DARK)
        for side, phase in ((-1, 0.), (1, .5)):
            overlay.light(frame.at(side * (half - 3), 5), OUTPOST_COLOR,
                          blinking(phase))
    if built >= 2:
        dome(overlay, frame, -half - 30)
        overlay.band(*frame.box(-half - 70, -half - 58, 12), STEEL, DARK)
        overlay.band(*frame.box(-half - 84, -half - 74, 9), STEEL, DARK)
    if built >= 3:
        towers(overlay, frame, half + 22)
    beacon(overlay, frame, half + 10 if built < 3 else half + 50)


def corners(overlay: Overlay, frame: Frame, half: float) -> None:
    """ Of the bare site, where the pad will be """
    for side in (-1, 1):
        overlay.band(
            *frame.box(side * half - 3, side * half + 3, 8), OUTPOST_COLOR,
        )


def beacon(overlay: Overlay, frame: Frame, along: float) -> None:
    overlay.band(*frame.box(along - 1, along + 1, 24), STEEL)
    overlay.light(frame.at(along, 26), OUTPOST_COLOR, blinking(0.))


def dome(overlay: Overlay, frame: Frame, along: float) -> None:
    """ Half an ellipse, flat on the ground """
    width, height = 22., 16.
    points = [frame.at(along - width, -2)] + [
        frame.at(along - width * math.cos(t), height * math.sin(t))
        for t in (math.pi * k / 12 for k in range(13))
    ]
    overlay.shape(points, GLASS, DARK)


def towers(overlay: Overlay, frame: Frame, along: float) -> None:
    """ Two towers, red lights on top, a dish between them """
    for offset, height, phase in ((0., 46., 0.), (16., 34., .5)):
        overlay.band(*frame.box(along + offset - 3, along + offset + 3,
                                height), STEEL, DARK)
        overlay.light(frame.at(along + offset, height + 2), RED,
                      blinking(phase))
    dish = [
        frame.at(along + 8 + 9 * math.cos(t), 24 + 6 * math.sin(t))
        for t in (math.pi * k / 8 for k in range(9))
    ]
    overlay.shape(dish, GLASS, DARK)


def draw_station(overlay: Overlay, outpost: Outpost) -> None:
    """ Its body unseen, the ring is as wide, its port on top """
    frame = Frame(outpost)
    center, radius = outpost.body.pos, outpost.body.radius
    built = outpost.construction.built
    if built == 0:
        overlay.circle(center, radius - 4, OUTPOST_COLOR, 1, .35)
        overlay.shape(around(center, 6), STEEL, DARK)
        overlay.light(center, OUTPOST_COLOR, blinking(0.))
        return
    for k in range(4):
        angle = outpost.direction + math.pi / 4 + k * math.pi / 2
        overlay.segment(
            point(center, angle, 10), point(center, angle, radius - 4),
            STEEL, 1.5,
        )
    overlay.circle(center, radius - 4, STEEL, 4 if built >= 2 else 1.5)
    overlay.shape(around(center, 10), STEEL, DARK)
    overlay.band(*frame.box(-8, 8, 6), STEEL, DARK)
    overlay.light(frame.at(0, 7), OUTPOST_COLOR, blinking(0.))
    if built >= 2:
        for k in range(12):
            angle = outpost.direction + (k + .5) * math.pi / 6
            overlay.light(point(center, angle, radius - 4), GLASS,
                          blinking(k / 12) * .8)
    if built >= 3:
        for side in (-1, 1):
            angle = outpost.direction + side * math.pi / 2
            overlay.segment(point(center, angle, radius),
                            point(center, angle, radius + 10), STEEL, 1.5)
            middle = point(center, angle, radius + 22)
            overlay.shape(around(middle, 14, 4), GLASS, DARK)
        foot = point(center, outpost.direction + math.pi, radius - 2)
        tip = point(center, outpost.direction + math.pi, radius + 18)
        overlay.segment(foot, tip, STEEL, 1.5)
        overlay.light(tip, RED, blinking(.5))


def point(center: Vec2, angle: float, distance: float) -> Vec2:
    return (
        center[0] + math.cos(angle) * distance,
        center[1] + math.sin(angle) * distance,
    )


def around(center: Vec2, wide: float,
           high: float | None = None) -> list[Vec2]:
    """ A box `wide` and `high` both ways, or a disc `wide` across """
    if high is not None:
        x, y = center
        return [
            (x - wide, y - high), (x + wide, y - high),
            (x + wide, y + high), (x - wide, y + high),
        ]
    return [point(center, math.pi * k / 8, wide) for k in range(16)]
