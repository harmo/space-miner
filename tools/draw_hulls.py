""" Drawings of the hulls, nose to the right: their slots are where the
parts attach, see app/logic/ship/hulls.py """

from .sketch import (
    ACCENT,
    EMITTER,
    GLASS,
    LINES,
    METAL,
    METAL_DARK,
    Sketch,
)


def draw_scout(sketch: Sketch) -> None:
    """ Small arrowhead, cockpit forward, an orange chevron behind """
    sketch.box(0, 5.5, 2.5, 10.5, METAL_DARK, radius=.5)
    sketch.polygon([
        (1, 4.5), (5, 1.5), (15, 1.5), (21, 3.5), (25.5, 8),
        (21, 12.5), (15, 14.5), (5, 14.5), (1, 11.5),
    ], METAL)
    sketch.line([(11, 2.3), (11, 13.7)], METAL_DARK, .4)
    sketch.polygon([
        (5.5, 1.8), (7.5, 1.8), (10, 8), (7.5, 14.2), (5.5, 14.2), (8, 8),
    ], ACCENT, outline=False)
    sketch.oval(14, 5.5, 21.5, 10.5, GLASS)
    sketch.glint(15.5, 6.3, 18.5, 7.6)


def draw_hauler(sketch: Sketch) -> None:
    """ Boxy, a small cockpit forward, orange bands around its hold """
    sketch.box(0, 7, 2.5, 15, METAL_DARK, radius=.5)
    sketch.polygon([
        (1, 4), (4, 1), (31, 1), (36, 4), (39.5, 11),
        (36, 18), (31, 21), (4, 21), (1, 18),
    ], METAL)
    for left in (9, 18):
        sketch.box(left, 1.4, left + 2.5, 20.6, ACCENT, outline=False)
    sketch.line([(15.2, 1.6), (15.2, 20.4)], METAL_DARK, .4)
    sketch.line([(24, 1.6), (24, 20.4)], METAL_DARK, .4)
    sketch.oval(29, 8, 35.5, 14, GLASS)
    sketch.glint(30.2, 8.8, 33, 10.3)


def draw_driller(sketch: Sketch) -> None:
    """ Armored wedge, its laser built in at the nose """
    sketch.box(0, 6, 2.5, 12, METAL_DARK, radius=.5)
    sketch.polygon([
        (1, 5), (6, 1), (20, 1), (28, 4), (31.5, 9),
        (28, 14), (20, 17), (6, 17), (1, 13),
    ], METAL)
    for top, bottom in ((1.4, 4.2), (13.8, 16.6)):
        sketch.box(7, top, 19, bottom, METAL_DARK, outline=False)
    for x in (5, 8):
        sketch.polygon([
            (x, 2), (x + 2, 2), (x + 4.5, 9), (x + 2, 16), (x, 16),
            (x + 2.5, 9),
        ], EMITTER, outline=False)
    sketch.oval(16, 6.5, 22, 11.5, GLASS)
    sketch.glint(17, 7.2, 19.6, 8.4)
    sketch.oval(26, 7, 30.5, 11, LINES)
    sketch.oval(27, 7.8, 29.6, 10.2, EMITTER, outline=False)


def draw_cruiser(sketch: Sketch) -> None:
    """ Long, a wide bridge forward, two chevrons behind """
    sketch.box(0, 7, 2.5, 19, METAL_DARK, radius=.5)
    sketch.polygon([
        (1, 6), (6, 1), (34, 1), (42, 5), (47.5, 13),
        (42, 21), (34, 25), (6, 25), (1, 20),
    ], METAL)
    for top, bottom in ((2.6, 4.6), (21.4, 23.4)):
        sketch.box(14, top, 30, bottom, METAL_DARK, outline=False)
    for x in (6, 13):
        sketch.polygon([
            (x, 1.6), (x + 2.5, 1.6), (x + 6, 13), (x + 2.5, 24.4),
            (x, 24.4), (x + 3.5, 13),
        ], ACCENT, outline=False)
    sketch.line([(24, 5), (24, 21)], METAL_DARK, .4)
    sketch.oval(32, 9, 41, 17, GLASS)
    sketch.glint(33.5, 10, 37.5, 11.6)
