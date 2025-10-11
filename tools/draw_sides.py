""" Drawings of the side parts, attached by their bottom edge, as drawn
for the left side """

from .sketch import (
    ACCENT,
    FLAME,
    ION,
    LINES,
    METAL,
    METAL_DARK,
    Color,
    Drawing,
    Sketch,
)


def draw_cargo_pod(sketch: Sketch) -> None:
    """ Container capsule on a pylon """
    sketch.box(6, 5, 12, 8, METAL_DARK)
    sketch.box(.5, .5, 17.5, 6, METAL, radius=2.7)
    sketch.box(4, .5, 14, 6, ACCENT)
    for x in (7.3, 10.7):
        sketch.line([(x, .8), (x, 5.7)], LINES, .4)
    sketch.glint(5, 1.2, 13, 2.4)


def draw_container(sketch: Sketch) -> None:
    """ Big capsule on two pylons """
    for x in (6, 15):
        sketch.box(x, 6.5, x + 3, 10, METAL_DARK)
    sketch.box(.5, .5, 23.5, 7.5, METAL, radius=3.4)
    sketch.box(4, .5, 20, 7.5, ACCENT)
    for x in (8, 12, 16):
        sketch.line([(x, .8), (x, 7.2)], LINES, .4)
    sketch.glint(5, 1.2, 19, 2.6)


def fins_drawing(light: Color) -> Drawing:
    def draw_fins(sketch: Sketch) -> None:
        """ Wing swept backwards, a light at its tip """
        sketch.polygon([
            (2.5, 8), (13, 8), (5.5, 1.2), (1.2, .5), (.6, 1.8),
        ], METAL)
        sketch.line([(5.5, 1.4), (11.8, 7.4)], ACCENT, .7)
        sketch.oval(.5, .3, 2.1, 1.9, light, outline=False)
    return draw_fins


def delta_wing_drawing(light: Color) -> Drawing:
    def draw_delta_wing(sketch: Sketch) -> None:
        """ Wide triangle along the hull, a light at its tip """
        sketch.polygon([(1, 9), (17, 9), (3.5, .8), (1, .6)], METAL)
        sketch.polygon(
            [(2, 8.6), (8, 8.6), (2.4, 4)], METAL_DARK, outline=False,
        )
        sketch.line([(4, 1.4), (16, 8.5)], ACCENT, .7)
        sketch.oval(.4, 0, 2, 1.6, light, outline=False)
    return draw_delta_wing


def draw_side_thruster(sketch: Sketch) -> None:
    """ Small pod with a nozzle pointing backwards """
    sketch.box(4, 5, 8, 8, METAL_DARK)
    sketch.polygon(
        [(2.5, 1.4), (.3, .6), (.3, 5.7), (2.5, 4.9)], METAL_DARK,
    )
    sketch.oval(0, 1.6, 1, 4.7, FLAME, outline=False)
    sketch.box(2, .8, 11.5, 5.5, METAL, radius=2.3)
    sketch.box(6, .8, 7.5, 5.5, ACCENT)


def draw_ion_pod(sketch: Sketch) -> None:
    """ Slim nacelle glowing blue """
    sketch.box(5, 5, 9, 8, METAL_DARK)
    sketch.polygon([(3, 1.3), (.4, .7), (.4, 5.3), (3, 4.7)], METAL_DARK)
    sketch.oval(0, 1.6, 1.1, 4.4, ION, outline=False)
    sketch.box(2.5, .8, 13.5, 5.2, METAL, radius=2.2)
    sketch.box(8, .8, 9.2, 5.2, ACCENT)


def draw_cargo_bay(sketch: Sketch) -> None:
    """ Armored container, two panels """
    for x in (4, 13):
        sketch.box(x, 7, x + 3, 10, METAL_DARK)
    sketch.box(.5, .5, 19.5, 7.5, METAL, radius=1.2)
    for left, right in ((2, 9.5), (10.5, 18)):
        sketch.box(left, 1.5, right, 6.5, ACCENT)
        sketch.line([(left + .3, 4), (right - .3, 4)], LINES, .3)


def draw_gyro(sketch: Sketch) -> None:
    """ Spinning disc """
    sketch.box(3.5, 4.5, 6.5, 7, METAL_DARK)
    sketch.oval(.8, .3, 9.2, 5.3, METAL)
    sketch.oval(2.5, 1.3, 7.5, 4.3, ACCENT)
    sketch.oval(4.3, 2.1, 5.7, 3.5, LINES)


def wing_pod_drawing(light: Color) -> Drawing:
    def draw_wing_pod(sketch: Sketch) -> None:
        """ Wing carrying a pod at its tip, a light in front """
        sketch.polygon([(2, 10), (20, 10), (9, 3.5), (3, 3.2)], METAL)
        sketch.line([(9.5, 4), (19, 9.5)], ACCENT, .7)
        sketch.box(1, .5, 15, 4.8, METAL, radius=2)
        sketch.box(5, .5, 9, 4.8, ACCENT)
        sketch.oval(14.2, 1.8, 15.6, 3.4, light, outline=False)
    return draw_wing_pod
