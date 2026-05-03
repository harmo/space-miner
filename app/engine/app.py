""" The Kivy application, which loads spaceminer.kv next to it """

from kivy.app import App

# The widgets of spaceminer.kv, the Game widget at its root
from .base.earth_base import EarthBase  # noqa: F401
from .game import Game  # noqa: F401
from .ui.cargo_panel import CargoPanel  # noqa: F401
from .ui.tracker import MissionTracker  # noqa: F401
from .ui.widgets import Layer, PanelButton  # noqa: F401


class SpaceMinerApp(App):
    pass
