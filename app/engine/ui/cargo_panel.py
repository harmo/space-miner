""" Panel showing the ore in the cargo, styled in cargo_panel.kv """

from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from ...logic.base.unloading import Depot
from ...logic.colors import Rgb
from ...logic.config import IMAGES
from ...logic.hud import cargo_color
from ...logic.mining.minerals import MINERALS, asteroid_texture
from ...logic.mining.ore import cargo_fill, cargo_lines, cargo_total
from ..ship.miner import Miner
from .widgets import load_style

ICON_SHAPE = 3                # round asteroid drawing


class CargoRow(BoxLayout):
    icon = StringProperty('')
    name = StringProperty('')
    amount = NumericProperty(0)
    color = ListProperty([1., 1., 1.])
    mining = BooleanProperty(False)


class CargoPanel(BoxLayout):
    """ How full the cargo is, then only what it holds, or "Vide". Also
    shows the depot on the Earth, without the bar. """

    title = StringProperty('SOUTE')
    bar = BooleanProperty(True)                # how full it is
    fill = NumericProperty(0)                  # from 0 to 1
    load = StringProperty('')
    bar_color = ListProperty([1., 1., 1.])

    def on_kv_post(self, base_widget: Widget) -> None:
        # Made once, shown when needed
        self.rows: dict[str, CargoRow] = {}
        for name, mineral in MINERALS.items():
            texture = asteroid_texture(name, ICON_SHAPE)
            self.rows[name] = CargoRow(
                icon=f'{IMAGES}/asteroids/minerals/{texture}.png',
                name=mineral.name, color=list(mineral.color),
            )
        self.shown: list[str] = []

    def show(self, ore: dict[str, float], mining: str | None, fill: float,
             load: str, bar_color: Rgb) -> None:
        """ `mining` is highlighted, as mined, or unloaded """
        self.fill = fill
        self.load = load
        self.bar_color = list(bar_color)
        lines = cargo_lines(ore, mining)
        minerals = [line.mineral for line in lines]
        if minerals != self.shown:
            for mineral in self.shown:
                self.remove_widget(self.rows[mineral])
            for mineral in minerals:
                self.add_widget(self.rows[mineral])
            self.shown = minerals
            self.ids.empty.opacity = 0 if minerals else 1
            self.ids.empty.height = 0 if minerals else self.ids.empty.line
        for line in lines:
            row = self.rows[line.mineral]
            row.amount = line.amount
            row.mining = line.mining


def show_cargo(panel: CargoPanel, miner: Miner,
               highlight: str | None) -> str:
    """ Returns how much it holds, as shown """
    fill = cargo_fill(miner.ore, miner.capacity)
    load = f'{cargo_total(miner.ore)} / {int(miner.capacity)}'
    panel.show(miner.ore, highlight, fill, load, cargo_color(fill))
    return load


def show_depot(panel: CargoPanel, depot: Depot) -> None:
    stock = depot.stock
    panel.show(stock, depot.mineral, 0., str(cargo_total(stock)), (1, 1, 1))


load_style(__file__)
