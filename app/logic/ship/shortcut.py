""" The shortcut shown near a ground, landing automatically """

from typing import Literal

from .config import LANDING_RANGE, SHORTCUT_RANGE
from .ground import GroundKind

# Hidden, shown but too far to be used, close enough but not above where
# the ship can land,
# or ready to be used
Shortcut = Literal['hidden', 'far', 'aside', 'ready']
# Told beside it
ASIDE: dict[GroundKind, str] = {
    'land': "Au-dessus de l'eau",
    'pad': 'Hors de la plateforme',
    'port': 'Hors du port',
}


def shortcut(distance: float, landed: bool, ground: bool) -> Shortcut:
    """ State of the shortcut at `distance` from the surface, above the
    `ground` or aside from it """
    if landed or distance > SHORTCUT_RANGE:
        return 'hidden'
    if distance > LANDING_RANGE:
        return 'far'
    return 'ready' if ground else 'aside'


def shortcut_text(state: Shortcut, kind: GroundKind) -> str:
    """ Shown on the shortcut, near that kind of ground """
    if state == 'aside':
        return ASIDE[kind]
    return "S'amarrer" if kind == 'port' else 'Atterrir'
