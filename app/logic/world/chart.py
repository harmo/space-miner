""" The map of the solar system: where things of the world go on it.
Whole, centered on the sun, its farthest orbit fitting in its frame, or
zoomed in on the ship. """

from dataclasses import dataclass

from .space import Vec2

MARGIN = .92                  # of the frame, the farthest orbit fills


ZOOMS = (1., 2., 4., 8.)


@dataclass(frozen=True)
class Chart:
    focus: Vec2               # in the world, in the middle of the map
    middle: Vec2              # of the map, on the screen
    scale: float              # screen pixels per world pixel

    def place(self, pos: Vec2) -> Vec2:
        return (
            self.middle[0] + (pos[0] - self.focus[0]) * self.scale,
            self.middle[1] + (pos[1] - self.focus[1]) * self.scale,
        )

    def size(self, length: float, smallest: float = 0.) -> float:
        """ On the map, never smaller than `smallest` to be seen """
        return max(smallest, length * self.scale)


def chart(
    sun: Vec2,
    farthest: float,
    middle: Vec2,
    frame: Vec2,
    zoom: float = 1.,
    ship: Vec2 | None = None
) -> Chart:
    """ `farthest` from the sun fitting in a `frame` around `middle`, or
    `zoom` times closer to the ship """
    half = min(frame) / 2
    focus = ship if zoom > 1 and ship is not None else sun
    return Chart(focus, middle, half * MARGIN / farthest * zoom)


def zoomed(zoom: float, closer: bool) -> float:
    """ The next zoom, closer or farther, the same at either end """
    index = ZOOMS.index(zoom) + (1 if closer else -1)
    return ZOOMS[max(0, min(index, len(ZOOMS) - 1))]
