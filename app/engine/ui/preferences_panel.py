""" Settings, from the home page: what is shown, the full screen, the
volumes of the sounds and of the ambience, and a new game, which takes a
confirmation. Styled in preferences_panel.kv. """

from typing import Any

from kivy.core.window import Window
from kivy.properties import BooleanProperty, NumericProperty
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
    sounds = NumericProperty(1.)
    ambience = NumericProperty(1.)
    mobile = BooleanProperty(False)         # always full screen

    def __init__(self, **kwargs: Any) -> None:
        self.register_event_type('on_close')
        super().__init__(**kwargs)
        self.preferences = Preferences()

    def on_close(self) -> None:
        """ The close button was pressed """

    def show(self, preferences: Preferences) -> None:
        self.preferences = preferences
        self.orbits = preferences.orbits
        self.markers = preferences.markers
        self.fullscreen = preferences.fullscreen
        self.sounds = preferences.sounds
        self.ambience = preferences.ambience

    def toggle(self, name: str) -> None:
        """ Of the preferences, saved at once """
        value = not getattr(self.preferences, name)
        setattr(self.preferences, name, value)
        setattr(self, name, value)
        if name == 'fullscreen':
            apply_fullscreen(value)
        write_preferences(self.preferences)

    def adjust(self, name: str, volume: float) -> None:
        """ A volume of the preferences, heard and saved at once """
        if getattr(self.preferences, name) != volume:
            setattr(self.preferences, name, volume)
            setattr(self, name, volume)
            write_preferences(self.preferences)


load_style(__file__)
