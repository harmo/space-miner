""" The Kivy application, which loads spaceminer.kv next to it """

from kivy.app import App

# The widgets of spaceminer.kv, the Game widget at its root
from .base.earth_base import EarthBase  # noqa: F401
from .game import Game
from .ui.cargo_panel import CargoPanel  # noqa: F401
from .ui.home_page import HomePage  # noqa: F401
from .ui.map_page import MapPage  # noqa: F401
from .ui.preferences_panel import PreferencesPanel  # noqa: F401
from .ui.scanner_panel import ScannerPanel  # noqa: F401
from .ui.tracker import MissionTracker  # noqa: F401
from .ui.widgets import Layer, PanelButton  # noqa: F401


class SpaceMinerApp(App):

    def on_pause(self) -> bool:
        """ Phones may close a paused app: the game is saved first """
        self.save()
        return True

    def on_stop(self) -> None:
        self.save()

    def save(self) -> None:
        if isinstance(self.root, Game):
            self.root.save()
