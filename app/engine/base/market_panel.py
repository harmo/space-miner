""" The market of the base, buying ore from the depot, for less than the
missions pay, and its refinery, crushing the rock of the depot. Styled
in market_panel.kv. """

from typing import Any

from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout

from ...logic.base.crushing import Crusher
from ...logic.base.market import ore_price, sell_ore
from ...logic.base.missions import Board, needs
from ...logic.base.wallet import Wallet
from ...logic.config import IMAGES
from ...logic.mining.minerals import MINERALS, asteroid_texture
from ...logic.mining.ore import whole_units
from ..ui.cargo_panel import ICON_SHAPE
from ..ui.widgets import load_style
from .missions_panel import credits_text

BATCH = 10                    # units sold by the smaller button


class OreRow(BoxLayout):
    panel = ObjectProperty(None)
    mineral = StringProperty('')
    icon = StringProperty('')
    name = StringProperty('')
    units = StringProperty('')
    price = StringProperty('')          # of a unit
    wanted = StringProperty('')         # by the missions under way
    batch = StringProperty('')          # sold by the smaller button
    batch_units = NumericProperty(BATCH)
    can_batch = BooleanProperty(False)


class MarketPanel(BoxLayout):

    money = StringProperty('')
    empty = BooleanProperty(True)
    rock = NumericProperty(0)           # units in the depot
    crushing = BooleanProperty(False)

    def __init__(self, **kwargs: Any) -> None:
        self.register_event_type('on_close')
        super().__init__(**kwargs)
        self.wallet = Wallet()
        self.stock: dict[str, float] = {}   # of the depot
        self.board: Board | None = None
        self.crusher: Crusher | None = None

    def on_close(self) -> None:
        """ The close button was pressed """

    def refresh(self) -> None:
        self.money = credits_text(self.wallet.credits)
        missions = self.board.active if self.board else []
        wanted = {need.mineral: need.wanted for need in needs(missions)}
        rows = self.ids.rows
        rows.clear_widgets()
        for name, mineral in MINERALS.items():
            units = whole_units(self.stock.get(name, 0.))
            if units <= 0:
                continue
            texture = asteroid_texture(name, ICON_SHAPE)
            rows.add_widget(OreRow(
                panel=self, mineral=name, name=mineral.name,
                icon=f'{IMAGES}/asteroids/minerals/{texture}.png',
                units=str(units),
                price=f'{credits_text(ore_price(name))} / u',
                wanted=f'missions : {wanted[name]}' if name in wanted else '',
                batch=f'Vendre {min(BATCH, units)}',
                can_batch=units > BATCH,
            ))
        self.empty = not rows.children
        self.rock = whole_units(self.stock.get('rock', 0.))
        self.crushing = self.crusher is not None and self.crusher.crushing

    def crush(self) -> None:
        """ The rock of the depot, at the refinery """
        if self.crusher is not None:
            self.crusher.start(self.stock)
        self.refresh()

    def sell(self, mineral: str, units: int | None = None) -> None:
        """ All of it without `units` """
        stock = self.stock
        sell_ore(
            stock, mineral, units or whole_units(stock.get(mineral, 0.)),
            self.wallet,
        )
        self.refresh()


load_style(__file__)
