""" The Kivy application, which loads spaceminer.kv next to it """

from kivy.app import App

# The widgets of spaceminer.kv, the Game widget at its root
from .game import Game  # noqa: F401
from .ui.cargo_panel import CargoPanel  # noqa: F401
from .ui.widgets import Layer, PanelButton  # noqa: F401


class SpaceMinerApp(App):
    pass
