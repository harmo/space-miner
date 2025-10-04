""" Drawings of the nose parts, attached by their left edge """

from .sketch import (
    ACCENT,
    EMITTER,
    GLASS,
    ION,
    LINES,
    METAL,
    METAL_DARK,
    NOZZLE,
    QUANTUM,
    STELLAR,
    Sketch,
)


def draw_laser(sketch: Sketch) -> None:
    sketch.box(0, .8, 5, 5.2, METAL_DARK, radius=1)
    sketch.box(4.5, 2, 11, 4, METAL)
    sketch.box(10.2, 1.5, 12, 4.5, LINES, radius=.4)
    sketch.oval(10.7, 2.4, 11.7, 3.6, EMITTER, outline=False)


def draw_heavy_laser(sketch: Sketch) -> None:
    """ Twin barrels """
    sketch.box(0, .5, 7, 8.5, METAL_DARK, radius=1.5)
    sketch.box(4.8, .9, 6.2, 8.1, ACCENT, outline=False)
    for top in (1.5, 5.5):
        sketch.box(6.5, top, 15, top + 2, METAL)
        sketch.box(14.2, top - .4, 16, top + 2.4, LINES, radius=.4)
        sketch.oval(14.6, top + .4, 15.6, top + 1.6, EMITTER, outline=False)


def draw_quantum_laser(sketch: Sketch) -> None:
    """ Long barrel wound with glowing coils """
    sketch.box(0, 1, 8, 10, METAL_DARK, radius=1.5)
    sketch.box(5.8, 1.4, 7.2, 9.6, ACCENT, outline=False)
    sketch.box(7.5, 3.8, 18, 7.2, METAL)
    for x in (9.5, 12, 14.5):
        sketch.box(x, 2.6, x + 1.2, 8.4, QUANTUM, radius=.4)
    sketch.box(17.4, 3, 20, 8, LINES, radius=.6)
    sketch.oval(18, 4.3, 19.4, 6.7, QUANTUM, outline=False)


def draw_nose_cone(sketch: Sketch) -> None:
    """ Streamlined cap, a sensor at its tip """
    sketch.polygon([(0, 2), (3, 1), (9, 6), (3, 11), (0, 10)], METAL)
    sketch.line([(3.2, 1.6), (8, 5.8)], ACCENT, .6)
    sketch.line([(3.2, 10.4), (8, 6.2)], ACCENT, .6)
    sketch.line([(.8, 6), (6.5, 6)], METAL_DARK, .4)
    sketch.oval(6.6, 5.2, 8.2, 6.8, GLASS, outline=False)


def draw_front_hold(sketch: Sketch) -> None:
    """ Crate with a rounded cap """
    sketch.box(9, 2, 12, 8, METAL_DARK, radius=1.2)
    sketch.box(0, 1, 10, 9, METAL, radius=1)
    sketch.box(3, 1, 9, 9, ACCENT)
    for x in (5, 7):
        sketch.line([(x, 1.3), (x, 8.7)], LINES, .4)


def draw_pulse_laser(sketch: Sketch) -> None:
    """ Short barrel, cooled by rings """
    sketch.box(0, 1, 6, 7, METAL_DARK, radius=1)
    sketch.box(5.5, 2.5, 12.5, 5.5, METAL)
    for x in (7, 9, 11):
        sketch.box(x, 2.1, x + .8, 5.9, ACCENT, outline=False)
    sketch.box(12, 2, 14, 6, LINES, radius=.4)
    sketch.oval(12.5, 3.2, 13.5, 4.8, ION, outline=False)


def draw_stellar_laser(sketch: Sketch) -> None:
    """ The biggest barrel, wound with burning coils """
    sketch.box(0, 1, 9, 11, METAL_DARK, radius=2)
    sketch.box(6.5, 1.4, 8, 10.6, ACCENT, outline=False)
    sketch.box(8.5, 4, 19, 8, METAL)
    for x in (10, 12.5, 15, 17.5):
        sketch.box(x, 2.8, x + 1.2, 9.2, STELLAR, radius=.4)
    sketch.box(18.5, 3, 22, 9, LINES, radius=.8)
    sketch.oval(19.3, 4.6, 21.2, 7.4, STELLAR, outline=False)


def draw_collector(sketch: Sketch) -> None:
    """ Scoop opening forwards """
    sketch.polygon([(0, 2), (4, 1), (12, 0), (12, 12), (4, 11), (0, 10)],
                   METAL)
    sketch.polygon([(5, 2.6), (11.4, 1.3), (11.4, 10.7), (5, 9.4)], NOZZLE)
    sketch.line([(3.6, 1.6), (3.6, 10.4)], ACCENT, .7)
