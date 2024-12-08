""" Kinds of asteroids: what they are made of, how they look and how hard
they are to mine """

from dataclasses import dataclass

from ..colors import Rgb, rgb
from ..ship.lasers import laser as laser_of


@dataclass(frozen=True)
class Mineral:
    name: str             # shown to the player
    the: str              # name with its article, in sentences
    lines: str            # colors of the asteroid drawing
    fill: str
    hardness: float       # mining takes this many times longer than rock
    laser: int            # level of laser needed to mine it at all
    frequency: float      # relative, in the asteroid belts
    glow: bool = False    # surrounded by a halo of its color

    @property
    def color(self) -> Rgb:
        """ Of the debris when mined out """
        return rgb(self.fill)


# From the most common to the rarest, as shown in the cargo
MINERALS = {
    'rock': Mineral(
        'Roche', 'la roche', '#6f6a63', '#b3ada4', 1., 1, 40.),
    'ice': Mineral(
        'Glace', 'la glace', '#4a86a8', '#c4e6f5', .6, 1, 14.),
    'iron': Mineral(
        'Fer', 'le fer', '#743a22', '#b8653e', 2., 1, 18.),
    'copper': Mineral(
        'Cuivre', 'le cuivre', '#2f6f5e', '#5fb39a', 1.5, 1, 12.),
    'gold': Mineral(
        'Or', "l'or", '#8f6d16', '#e6c040', 4., 1, 8.),
    'crystal': Mineral(
        'Cristal', 'le cristal', '#5e3593', '#c19ae6', 3., 2, 4.),
    'uranium': Mineral(
        'Uranium', "l'uranium", '#4f7d12', '#a6e22e', 2.5, 2, 3., glow=True),
    'helium3': Mineral(
        'Hélium-3', "l'hélium-3", '#1f7f8f', '#6ff0ff', 2., 2, 2.5,
        glow=True),
    'ruby': Mineral(
        'Rubis', 'le rubis', '#7d1426', '#e0475e', 5., 3, 1.5),
    'nebulite': Mineral(
        'Nébulite', 'la nébulite', '#8a1f6e', '#ff7ad9', 3.5, 3, 1.5,
        glow=True),
    'stellarium': Mineral(
        'Stellarium', 'le stellarium', '#a34a0b', '#ffa23a', 4., 3, 1.,
        glow=True),
    'antimatter': Mineral(
        'Antimatière', "l'antimatière", '#2a2f8c', '#8f9bff', 6., 4, .5,
        glow=True),
}

# Images of glowing minerals are this much bigger, to hold the halo
GLOW_SCALE = 1.4

# Drawings of the asteroids, the 4th one is the Moon
ASTEROID_SHAPES = (1, 2, 3, 5, 6)


def asteroid_texture(mineral: str, shape: int) -> str:
    return f'{mineral}_{shape}'


def display_scale(mineral: str | None) -> float:
    """ Size of the asteroid image relative to the asteroid itself """
    glows = mineral is not None and MINERALS[mineral].glow
    return GLOW_SCALE if glows else 1.


def mining_rate(mineral: Mineral, laser: int, base_rate: float) -> float:
    """ Ore extracted per second, none when the laser is too weak, faster
    with a more powerful one """
    if laser < mineral.laser:
        return 0.
    return base_rate * laser_of(laser).power / mineral.hardness
