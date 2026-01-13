""" The landing shortcut, a button shown near the Earth """

from kivy.uix.widget import Widget

from ...logic.hud import pulse
from ...logic.ship.config import SHORTCUT_PULSE
from ...logic.ship.landing import Shortcut

OPACITY = {'hidden': 0., 'far': .45, 'water': .45, 'ready': 1.}


def show_shortcut(button: Widget, state: Shortcut, time: float) -> float:
    """ Faded when too far to be used or above the water. Returns how much
    its outline glows: pulsing when usable. """
    button.opacity = OPACITY[state]
    button.text = "Au-dessus de l'eau" if state == 'water' else 'Atterrir'
    button.disabled = state != 'ready'
    if state == 'ready':
        return .45 + .55 * pulse(time, SHORTCUT_PULSE)
    return .3
