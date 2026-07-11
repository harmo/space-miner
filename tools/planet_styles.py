""" The character of each planet other than the Earth, see
draw_planets.py """

from collections.abc import Sequence
from dataclasses import dataclass, field

from .paint import Color, hex_color


def colors(*values: str) -> tuple[Color, ...]:
    return tuple(hex_color(value) for value in values)


@dataclass(frozen=True)
class Storm:
    """ An oval in the bands """
    at: tuple[float, float]   # from the center, in radii, y down
    size: tuple[float, float]  # across, in radii
    color: Color


@dataclass(frozen=True)
class Style:
    stops: tuple[Color, ...]  # of the bands, from pole to pole
    air: Color                # of the atmosphere on the edge
    bands: float = 3.         # times the stops are gone through
    swirl: float = .2         # how much the bands wave
    rocky: bool = False       # terrain rather than bands
    storms: tuple[Storm, ...] = ()
    streaks: float = 0.       # light clouds drawn out along the bands
    craters: int = 0
    caps: bool = False        # of ice, at the poles
    ring: Sequence[Color] = field(default_factory=tuple)
    glow: float = .55         # of the atmosphere, none without one
    seas: float = .6          # how much the plains of rocky worlds show
    sea: Color | None = None  # their color, the darkest stop without it
    shadow: Color = (40, 20, 15)  # in the craters


STYLES = {
    # Gas giant, banded in cream and brown, a great storm in the south
    'planet1': Style(
        colors('#e3cfa6', '#b9845a', '#ecdcbc', '#9c6640', '#d8ad7c'),
        hex_color('#f0d8b0'), bands=3.5, swirl=.12,
        storms=(Storm((.32, .3), (.34, .2), hex_color('#a8563c')),),
    ),
    # Rocky and rusty, dark plains, craters and a polar cap
    'planet2': Style(
        colors('#6e3424', '#9c4a2e', '#c0673e', '#d48a5a'),
        hex_color('#e0a080'), rocky=True, craters=9, caps=True,
    ),
    # Ice giant, smooth cyan, its bands hardly seen
    'planet3': Style(
        colors('#82c8cc', '#74b9bf', '#93d4d6', '#7ac0c6'),
        hex_color('#c8f2f4'), bands=2., swirl=.08, streaks=.25,
    ),
    # Violet giant, its bands stormy
    'planet4': Style(
        colors('#a585d4', '#7a5aae', '#bba2e2', '#64468f', '#9273c6'),
        hex_color('#d8c4f4'), bands=6., swirl=.16,
    ),
    # Wrapped in pink and cream clouds
    'planet5': Style(
        colors('#e3b4a8', '#d59a90', '#efcfc2', '#c9867f'),
        hex_color('#f6dcd2'), bands=1.5, swirl=.5, streaks=.35,
    ),
    # Pale gold, ringed
    'planet6': Style(
        colors('#eedcaa', '#d9be80', '#f4e6c0', '#cfae6e'),
        hex_color('#f4e8c4'), bands=4., swirl=.08,
        ring=colors('#c9b07a', '#e6d4a4', '#a8916a', '#ddc996'),
    ),
    # Deep blue, a dark storm and bright streaks of clouds
    'planet7': Style(
        colors('#4a68c8', '#3550a8', '#5a7ad4', '#2e4596'),
        hex_color('#9fb6f0'), bands=2.5, swirl=.15, streaks=.5,
        storms=(Storm((-.25, .15), (.3, .16), hex_color('#1e2c6a')),),
    ),
    # The Moon of the Earth: grey, dark seas and craters, no air
    'moon': Style(
        colors('#8e9094', '#a6a8ab', '#bdbfc2', '#cfd1d3'),
        hex_color('#ffffff'), rocky=True, craters=26, glow=0.,
        seas=.9, sea=hex_color('#62646a'), shadow=(25, 25, 30),
    ),
}
