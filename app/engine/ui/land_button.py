""" The landing shortcut, a button shown near ground, or the docking one
near stations """

from kivy.uix.widget import Widget

from ...logic.hud import pulse
from ...logic.ship.config import SHORTCUT_PULSE
from ...logic.ship.landing import GroundKind, Shortcut, shortcut_text

OPACITY = {'hidden': 0., 'far': .45, 'aside': .45, 'ready': 1.}


def show_shortcut(button: Widget, state: Shortcut, kind: GroundKind,
                  time: float) -> float:
    """ Faded when too far to be used or aside from where the ship can
    land. Returns how much its outline glows: pulsing when usable. """
    button.opacity = OPACITY[state]
    button.text = shortcut_text(state, kind)
    button.disabled = state != 'ready'
    if state == 'ready':
        return .45 + .55 * pulse(time, SHORTCUT_PULSE)
    return .3
