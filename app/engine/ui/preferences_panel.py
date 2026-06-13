""" Settings, from the home page: what is shown, the full screen, and a
new game, which takes a confirmation. Styled in preferences_panel.kv. """

from typing import Any

from kivy.core.window import Window
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout

from ...logic.preferences import Preferences
from ..storage import write_preferences
from .widgets import load_style

WINDOWED = (1280, 720)        # leaving the full screen, as main.py opens it


def apply_fullscreen(on: bool) -> None:
    Window.fullscreen = 'auto' if on else False
    if not on:
        Window.size = WINDOWED


class PreferencesPanel(BoxLayout):

    orbits = BooleanProperty(True)
    markers = BooleanProperty(True)
    fullscreen = BooleanProperty(True)
    confirming = BooleanProperty(False)     # a new game, once asked
    mobile = BooleanProperty(False)         # always full screen

    def __init__(self, **kwargs: Any) -> None:
        for event in ('on_close', 'on_new_game'):
            self.register_event_type(event)
        super().__init__(**kwargs)
        self.preferences = Preferences()

    def on_close(self) -> None:
        """ The close button was pressed """

    def on_new_game(self) -> None:
        """ A new game was confirmed """

    def show(self, preferences: Preferences) -> None:
        self.preferences = preferences
        self.orbits = preferences.orbits
        self.markers = preferences.markers
        self.fullscreen = preferences.fullscreen
        self.confirming = False

    def toggle(self, name: str) -> None:
        """ Of the preferences, saved at once """
        value = not getattr(self.preferences, name)
        setattr(self.preferences, name, value)
        setattr(self, name, value)
        if name == 'fullscreen':
            apply_fullscreen(value)
        write_preferences(self.preferences)

    def new_game(self) -> None:
        if self.confirming:
            self.confirming = False
            self.dispatch('on_new_game')
        else:
            self.confirming = True


load_style(__file__)
