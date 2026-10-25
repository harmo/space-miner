""" The map over the game, which stands still behind it: the map itself,
its zoom, and a button to close it. Styled in map_page.kv. """

from ..ship.player import Player
from ..world.solar_system import SolarSystem
from .map_view import MapView  # noqa: F401  (in the kv file)
from .widgets import Layer, load_style


class MapPage(Layer):

    __events__ = ('on_close',)

    def show(self, system: SolarSystem, player: Player) -> None:
        self.ids.view.show(system, player)

    def on_close(self) -> None:
        """ From its button: the game closes it """


load_style(__file__)
