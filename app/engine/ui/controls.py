""" What the keys and the touches of the player do in the game, besides
the buttons of the interface """

from typing import TYPE_CHECKING

from kivy.input.motionevent import MotionEvent

from ...logic.ship.config import PICK_RADIUS
from .pointer import on_any

if TYPE_CHECKING:
    from ..game import Game


def escape(game: 'Game') -> bool:
    """ Closes what is open over the game, or else pauses or resumes it.
    On the home page before playing, does nothing: Kivy leaves the game. """
    base, scanner = game.ids.base, game.ids.scanner
    if game.settings_open:
        game.settings_open = False
    elif game.map_open:
        game.map_open = False
    elif scanner.open:
        scanner.open = False
    elif base.panel:
        base.close()
    elif game.playing:
        game.pause()
    elif game.paused:
        game.resume()
    else:
        return False
    return True


def steers(game: 'Game', touch: MotionEvent) -> bool:
    """ Pressing a canister picks it up, pressing an asteroid locks the
    ship on it: whether the touch thrusts towards the pointer instead.
    Nothing on the buttons, nor while landing. """
    ids, player = game.ids, game.player
    buttons = [
        ids.land_button, ids.cargo_button, ids.scanner_button,
        ids.map_button, *ids.base.buttons,
    ]
    ship = player.ship
    if on_any(buttons, touch.pos) or ship is None or player.landing:
        return False
    camera = game.camera
    world = camera.convert_from_screen_to_world(touch.pos)
    tolerance = PICK_RADIUS * camera.camera_scale
    return not player.miner.work_at(world, tolerance, ship.position)
