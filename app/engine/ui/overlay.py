""" Drawn over the game in screen pixels: markers, orbits, locks, laser and
explosions """

import math
from collections.abc import Iterable
from typing import Any

from kivy.graphics import (
    Color,
    InstructionGroup,
    Line,
    Mesh,
    Point,
    Rectangle,
)

from ...logic.colors import Rgb
from ...logic.config import (
    CHEVRON_MARGIN,
    CHEVRON_WIDTH,
    MARKER_MARGIN,
    MARKER_OPACITY,
    MARKER_THICKNESS,
    ORBIT_DOT_SIZE,
    ORBIT_OPACITY,
)
from ...logic.hud import edge_point, is_on_screen, marker_length
from ...logic.ship.config import LEG_COLOR, LEG_OUTLINE
from ...logic.ship.lasers import Laser
from ...logic.ship.legs import Leg
from ...logic.world.explosion import Explosion
from ...logic.world.space import Celestial, Round, Vec2
from ..textures import make_texture, star_pixel

SOFT_DOT = 1.8               # size of the dots of the sparks, times theirs
CHEVRON_OPENING = math.radians(40)    # between each arm and its axis
CHEVRON_THICKNESS = .45               # of the V, for its size


class Overlay:
    """ Redrawn on each frame: call begin(), then the drawing methods """

    def __init__(self, canvas: Any, camera: Any) -> None:
        self.group = InstructionGroup()
        canvas.add(self.group)
        self.camera = camera
        self.size: Vec2 = (0., 0.)
        self.dot = make_texture(16, star_pixel)

    def begin(self, size: Vec2) -> None:
        self.group.clear()
        self.size = size

    def to_screen(self, pos: Vec2) -> Vec2:
        scale = self.camera.camera_scale
        camera_x, camera_y = self.camera.camera_pos
        return (pos[0] + camera_x) / scale, (pos[1] + camera_y) / scale

    def marker(self, target: Round, color: Rgb) -> None:
        """ Bar on the screen edge towards a target out of the screen,
        longer as it gets closer """
        width, height = self.size
        scale = self.camera.camera_scale
        center_x, center_y = self.camera.get_camera_center()
        dx = target.pos[0] - center_x
        dy = target.pos[1] - center_y
        if is_on_screen(
            (dx, dy), target.radius, (width * scale / 2, height * scale / 2)
        ):
            return

        (edge_x, edge_y), on_side = edge_point(
            math.atan2(dy, dx),
            (width / 2 - MARKER_MARGIN, height / 2 - MARKER_MARGIN),
        )
        length = marker_length(math.hypot(dx, dy))
        if on_side:
            bar_width, bar_height = MARKER_THICKNESS, length
        else:
            bar_width, bar_height = length, MARKER_THICKNESS
        x = min(max(width / 2 + edge_x - bar_width / 2, MARKER_MARGIN),
                width - MARKER_MARGIN - bar_width)
        y = min(max(height / 2 + edge_y - bar_height / 2, MARKER_MARGIN),
                height - MARKER_MARGIN - bar_height)
        self.group.add(Color(*color, MARKER_OPACITY))
        self.group.add(Rectangle(pos=(x, y), size=(bar_width, bar_height)))

    def wave(self, center: Vec2, radius: float, color: Rgb,
             opacity: float) -> None:
        """ A ring around `center`, `radius` in the world """
        x, y = self.to_screen(center)
        self.group.add(Color(*color, opacity))
        self.group.add(Line(
            circle=(x, y, radius / self.camera.camera_scale), width=3,
        ))

    def shape(self, points: list[Vec2], color: Rgb,
              outline: Rgb | None = None) -> None:
        """ A convex polygon of the world, filled """
        screen = [self.to_screen(point) for point in points]
        self.group.add(Color(*color, 1))
        self.group.add(Mesh(
            vertices=[value for x, y in screen for value in (x, y, 0, 0)],
            indices=list(range(len(screen))), mode='triangle_fan',
        ))
        if outline is not None:
            self.group.add(Color(*outline, 1))
            self.group.add(Line(
                points=[value for point in screen for value in point],
                width=1, close=True,
            ))

    def band(self, lower: list[Vec2], upper: list[Vec2], color: Rgb,
             outline: Rgb | None = None) -> None:
        """ Between two lines of the world, as many points each, filled
        even where it bends """
        lower = [self.to_screen(point) for point in lower]
        upper = [self.to_screen(point) for point in upper]
        strip = [
            value for low, up in zip(lower, upper, strict=True)
            for point in (low, up) for value in (*point, 0, 0)
        ]
        self.group.add(Color(*color, 1))
        self.group.add(Mesh(
            vertices=strip, indices=list(range(2 * len(lower))),
            mode='triangle_strip',
        ))
        if outline is not None:
            self.group.add(Color(*outline, 1))
            self.group.add(Line(
                points=[
                    value for point in lower + upper[::-1]
                    for value in point
                ],
                width=1, close=True,
            ))

    def light(self, pos: Vec2, color: Rgb, opacity: float) -> None:
        """ A dot of light, as big whatever the zoom """
        self.group.add(Color(*color, opacity))
        self.group.add(Point(points=self.to_screen(pos), pointsize=2.5))

    def dots(self, dots: list[Vec2]) -> None:
        """ Faint dots, as in a dotted orbit """
        points: list[float] = []
        for dot in dots:
            points.extend(self.to_screen(dot))
        if points:
            self.group.add(Color(1, 1, 1, ORBIT_OPACITY))
            self.group.add(Point(points=points, pointsize=ORBIT_DOT_SIZE))

    def chevron(self, target: Celestial, color: Rgb, size: float,
                opacity: float) -> None:
        """ Thick V on the screen edge pointing towards a target out of the
        screen, inside the bars: outlined only, to stay discreet """
        width, height = self.size
        scale = self.camera.camera_scale
        center_x, center_y = self.camera.get_camera_center()
        dx = target.pos[0] - center_x
        dy = target.pos[1] - center_y
        if is_on_screen(
            (dx, dy), target.radius, (width * scale / 2, height * scale / 2)
        ):
            return
        direction = math.atan2(dy, dx)
        (edge_x, edge_y), _ = edge_point(direction, (
            width / 2 - CHEVRON_MARGIN, height / 2 - CHEVRON_MARGIN,
        ))
        tip = (width / 2 + edge_x, height / 2 + edge_y)
        # The inner edge of the V, as far behind as it is thick
        back = (-math.cos(direction) * size * CHEVRON_THICKNESS,
                -math.sin(direction) * size * CHEVRON_THICKNESS)
        arms = []
        for side in (-1, 1):
            turn = direction + math.pi + side * CHEVRON_OPENING
            arms.append((
                tip[0] + math.cos(turn) * size,
                tip[1] + math.sin(turn) * size,
            ))
        outer = [arms[0], tip, arms[1]]
        inner = [(x + back[0], y + back[1]) for x, y in reversed(outer)]
        self.group.add(Color(*color, opacity))
        self.group.add(Line(
            points=[value for point in outer + inner for value in point],
            width=CHEVRON_WIDTH, close=True, joint='miter',
        ))

    def lock(self, target: Round, progress: float, color: Rgb) -> None:
        """ Circle around the target of the ship, with the mined part in
        the color of the laser """
        x, y = self.to_screen(target.pos)
        radius = target.radius / self.camera.camera_scale + 8
        self.group.add(Color(1, 1, 1, .35))
        self.group.add(Line(circle=(x, y, radius), width=1))
        if progress > 0:
            self.group.add(Color(*color, .9))
            self.group.add(Line(
                circle=(x, y, radius, 0, 360 * progress), width=1.5
            ))

    def laser(self, start: Vec2, end: Vec2, laser: Laser,
              strong: bool = True) -> None:
        """ Brighter and wider with its level. A laser too weak to mine is
        faint. """
        points = [*self.to_screen(start), *self.to_screen(end)]
        if not strong:
            self.group.add(Color(*laser.color, .3))
            self.group.add(Line(points=points, width=1.))
            return
        if laser.halo:
            self.group.add(Color(*laser.color, .22))
            self.group.add(Line(points=points, width=laser.width * 2.5))
        self.group.add(Color(*laser.color, .9))
        self.group.add(Line(points=points, width=laser.width))
        if laser.core:
            self.group.add(Color(1, 1, 1, .85))
            self.group.add(Line(points=points, width=laser.width / 3))

    def legs(self, legs: list[Leg], angle: float) -> None:
        """ Struts, outlined like the drawings of the ship, ending in pads
        across the ship """
        scale = self.camera.camera_scale
        across = (-math.sin(angle) * 1.5, math.cos(angle) * 1.5)
        for hip, foot in legs:
            pad = [
                *self.to_screen((foot[0] - across[0], foot[1] - across[1])),
                *self.to_screen((foot[0] + across[0], foot[1] + across[1])),
            ]
            strut = [*self.to_screen(hip), *self.to_screen(foot)]
            for color, width in ((LEG_OUTLINE, 1.), (LEG_COLOR, .55)):
                self.group.add(Color(*color, 1.))
                self.group.add(Line(points=strut, width=width / scale))
                self.group.add(Line(
                    points=pad, width=width / scale, cap='round',
                ))

    def sparks(self, sparks: Iterable[tuple[Vec2, Rgb, float, float]]
               ) -> None:
        """ Soft dots of a color, an opacity and a size in pixels of the
        world """
        scale = self.camera.camera_scale
        for pos, color, alpha, size in sparks:
            x, y = self.to_screen(pos)
            # The dot fades out towards its edge, it looks smaller
            side = SOFT_DOT * size / scale
            self.group.add(Color(*color, alpha))
            self.group.add(Rectangle(
                pos=(x - side / 2, y - side / 2), size=(side, side),
                texture=self.dot,
            ))

    def explosion(self, explosion: Explosion) -> None:
        fade = 1. - explosion.progress
        size = 2. + 5. * fade
        self.group.add(Color(*explosion.color, fade))
        for fragment in explosion.fragments:
            x, y = self.to_screen((fragment.x, fragment.y))
            self.group.add(Rectangle(
                pos=(x - size / 2, y - size / 2), size=(size, size)
            ))
