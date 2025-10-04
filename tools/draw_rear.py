""" Drawings of the rear parts, attached by their right edge """

from .sketch import (
    ACCENT,
    FLAME,
    FUSION,
    GLASS,
    ION,
    LINES,
    METAL,
    METAL_DARK,
    NOZZLE,
    SOLAR,
    WHITE_HOT,
    Sketch,
)


def draw_engine(sketch: Sketch) -> None:
    """ Bell nozzle flaring backwards, glowing inside """
    sketch.box(6, 2.5, 10, 9.5, METAL_DARK)
    sketch.polygon([
        (7, 2.5), (1.5, .5), (.3, 1.5), (.3, 10.5), (1.5, 11.5), (7, 9.5),
    ], METAL)
    for x in (3.8, 5.4):
        sketch.line([(x, 1.6), (x, 10.4)], METAL_DARK, .4)
    sketch.oval(0, 2, 2.2, 10, NOZZLE)
    sketch.oval(.4, 3.6, 1.6, 8.4, FLAME, outline=False)


def draw_ion_engine(sketch: Sketch) -> None:
    """ Long and slim, glowing blue """
    sketch.box(10, 2, 14, 8, METAL_DARK)
    sketch.polygon([
        (11, 2), (3, 1), (.5, 2.5), (.5, 7.5), (3, 9), (11, 8),
    ], METAL)
    for x in (5, 7, 9):
        sketch.line([(x, 1.6), (x, 8.4)], METAL_DARK, .4)
    sketch.oval(0, 2.5, 2, 7.5, NOZZLE)
    sketch.oval(.3, 3.5, 1.5, 6.5, ION, outline=False)


def draw_twin_engine(sketch: Sketch) -> None:
    """ Two bell nozzles on a common mount """
    sketch.box(8, 3, 12, 12, METAL_DARK)
    for top in (.5, 8):
        sketch.polygon([
            (9, top + 1.5), (2, top), (.3, top + 1), (.3, top + 5.5),
            (2, top + 6.5), (9, top + 5),
        ], METAL)
        sketch.oval(0, top + 1, 2, top + 5.5, NOZZLE)
        sketch.oval(.3, top + 2, 1.4, top + 4.5, FLAME, outline=False)
    sketch.box(7, 6, 9, 9, ACCENT)


def draw_vector_nozzle(sketch: Sketch) -> None:
    """ Small nozzle between two steering flaps """
    sketch.box(5, 2.5, 8, 7.5, METAL_DARK)
    sketch.polygon([(5, 2.5), (1, .5), (.5, 2), (4, 4)], METAL)
    sketch.polygon([(5, 7.5), (1, 9.5), (.5, 8), (4, 6)], METAL)
    sketch.box(1.5, 3.5, 5, 6.5, METAL)
    sketch.oval(1, 3.5, 2.6, 6.5, NOZZLE)
    sketch.oval(1.3, 4.2, 2.2, 5.8, FLAME, outline=False)


def draw_rear_hold(sketch: Sketch) -> None:
    """ Crate strapped behind the hull """
    sketch.box(10, 3, 12, 9, METAL_DARK)
    sketch.box(.5, .5, 11, 11.5, METAL, radius=1.5)
    sketch.box(2, 1.5, 9.5, 10.5, ACCENT)
    for y in (4.5, 7.5):
        sketch.line([(2.3, y), (9.2, y)], LINES, .4)


def draw_afterburner(sketch: Sketch) -> None:
    """ Long tube, burning white hot """
    sketch.box(8, 2.5, 12, 8.5, METAL_DARK)
    sketch.box(2, 2, 9, 9, METAL)
    for x in (4, 6):
        sketch.line([(x, 2.3), (x, 8.7)], METAL_DARK, .4)
    sketch.oval(.5, 1.5, 3, 9.5, NOZZLE)
    sketch.oval(.8, 3, 2.4, 8, FLAME, outline=False)
    sketch.oval(1.1, 4.2, 2, 6.8, WHITE_HOT, outline=False)


def draw_solar_sail(sketch: Sketch) -> None:
    """ Two panels on a mast """
    sketch.box(7, 7, 10, 11, METAL_DARK)
    sketch.line([(7.5, 9), (2, 9)], METAL_DARK, .8)
    for top, bottom in (((1, .5), (1, 8.5)), ((1, 17.5), (1, 9.5))):
        near = 8 if top[1] < 9 else 10
        far = 2 if top[1] < 9 else 16
        sketch.polygon([top, (6, far), (6, near), bottom], SOLAR)
        sketch.line([(3.5, top[1] + (1 if top[1] < 9 else -1)),
                     (3.5, bottom[1])], GLASS, .3)


def draw_fusion_engine(sketch: Sketch) -> None:
    """ Round chamber, a wide nozzle glowing pale blue """
    sketch.box(10, 3, 14, 11, METAL_DARK)
    sketch.oval(5, 1.5, 12, 12.5, METAL)
    sketch.box(8.5, 2, 9.5, 12, ACCENT, outline=False)
    sketch.polygon([
        (6, 3.5), (1, 1), (.3, 2), (.3, 12), (1, 13), (6, 10.5),
    ], METAL_DARK)
    sketch.oval(0, 2, 2.4, 12, NOZZLE)
    sketch.oval(.4, 3.8, 1.8, 10.2, FUSION, outline=False)
    sketch.oval(.7, 5.5, 1.5, 8.5, ION, outline=False)
    sketch.line([(4, 1.6), (4, 12.4)], LINES, .3)
