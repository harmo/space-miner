""" The home page, over the game which runs behind it, or is paused: to
play or resume, the settings, and quitting on computers. Styled in
home_page.kv. """

from kivy.properties import BooleanProperty

from .widgets import Layer, load_style


class HomePage(Layer):

    compact = BooleanProperty(False)        # tighter, as on phones
    paused = BooleanProperty(False)         # a game to resume
    mobile = BooleanProperty(False)         # apps closed from the system
    settings_open = BooleanProperty(False)  # over it, hiding it

    __events__ = ('on_play', 'on_settings')

    def on_play(self) -> None:
        """ Playing, or resuming the paused game """

    def on_settings(self) -> None:
        """ Opening them """


load_style(__file__)
