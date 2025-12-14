""" The pointer, a mouse or a finger, steering the ship """

import math
from collections.abc import Sequence
from typing import Any

from kivy.uix.widget import Widget

from ...logic.world.space import Vec2


def pointer_heading(camera: Any, pointer: Vec2 | None) -> float | None:
    """ Direction of the pointer while pressed. Aimed from the view center
    rather than from the ship: the camera lags behind the ship, which would
    make the heading flip when holding the pointer close to it. """
    if pointer is None:
        return None
    px, py = camera.convert_from_screen_to_world(pointer)
    cx, cy = camera.get_camera_center()
    if math.hypot(px - cx, py - cy) <= 1.:
        return None
    return math.atan2(py - cy, px - cx)


def on_any(widgets: Sequence[Widget], pos: Vec2) -> bool:
    """ Whether `pos` is on one of the widgets shown """
    return any(
        widget.opacity > 0 and widget.collide_point(*pos)
        for widget in widgets
    )
