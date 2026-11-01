""" The depot of a post: its ore, loaded back into the ship, sold if the
post has a market, crushed if it has a refinery, and sent away if it has a
dock. Styled in market_panel.kv. """

from typing import Any

from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout

from ...logic.base.board import Board
from ...logic.base.crushing import Crusher
from ...logic.base.market import ore_price, sell_ore
from ...logic.base.missions import needs
from ...logic.base.sites import Trade
from ...logic.base.unloading import Depot, load_ore
from ...logic.base.wallet import Wallet
from ...logic.config import IMAGES
from ...logic.mining.minerals import MINERALS, asteroid_texture
from ...logic.mining.ore import Hold, cargo_room, whole_units
from ..ship.miner import Miner
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
    can_load = BooleanProperty(False)   # the cargo has room
    selling = BooleanProperty(True)     # with a market


class MarketPanel(BoxLayout):

    money = StringProperty('')
    empty = BooleanProperty(True)
    rock = NumericProperty(0)           # units in the depot
    crushing = BooleanProperty(False)
    refinery = BooleanProperty(True)    # if the post has one
    refinery_told = StringProperty('')
    selling = BooleanProperty(True)     # or the depot alone
    shuttles = BooleanProperty(False)   # a dock, with somewhere to send to

    def __init__(self, **kwargs: Any) -> None:
        self.register_event_type('on_close')
        self.register_event_type('on_dock')
        super().__init__(**kwargs)
        self.wallet = Wallet()
        self.stock: Hold = {}   # of the depot
        self.board: Board | None = None
        self.crusher: Crusher | None = None
        self.prices = Trade()               # those of the Earth
        self.depot: Depot | None = None     # holding the stock
        self.miner: Miner | None = None     # of the ship, for its cargo
        # Made once, as they are slow to make and refreshed as ore is found
        self.ore_rows: dict[str, OreRow] = {}
        self.listed: list[str] = []         # the minerals shown

    def on_close(self) -> None:
        """ The close button was pressed """

    def on_dock(self) -> None:
        """ Those of the dock are asked for """

    def refresh(self) -> None:
        self.money = credits_text(self.wallet.credits)
        missions = self.board.active if self.board else []
        wanted = {need.mineral: need.wanted for need in needs(missions)}
        held = {
            name: whole_units(self.stock.get(name, 0.)) for name in MINERALS
        }
        listed = [name for name, units in held.items() if units > 0]
        rows = self.ids.rows
        if listed != self.listed:
            rows.clear_widgets()
            for name in listed:
                rows.add_widget(self.row(name))
            self.listed = listed
        for name in listed:
            units, row = held[name], self.ore_rows[name]
            row.units = str(units)
            row.price = f'{credits_text(self.price(name))} / u'
            row.wanted = (
                f'missions : {wanted[name]}' if name in wanted else ''
            )
            row.batch = f'Vendre {min(BATCH, units)}'
            row.can_batch = units > BATCH
            row.can_load = self.room >= 1
            row.selling = self.selling
        self.empty = not listed
        self.rock = whole_units(self.stock.get('rock', 0.))
        self.refinery = self.crusher is not None
        if self.crusher is not None:
            self.refinery_told = self.crusher.refinery.told
        self.crushing = self.crusher is not None and self.crusher.crushing

    def row(self, mineral: str) -> OreRow:
        if mineral not in self.ore_rows:
            texture = asteroid_texture(mineral, ICON_SHAPE)
            self.ore_rows[mineral] = OreRow(
                panel=self, mineral=mineral, name=MINERALS[mineral].name,
                icon=f'{IMAGES}/asteroids/minerals/{texture}.png',
            )
        return self.ore_rows[mineral]

    @property
    def room(self) -> float:
        """ In the cargo of the ship """
        miner = self.miner
        return cargo_room(miner.ore, miner.capacity) if miner else 0.

    def load(self, mineral: str) -> None:
        """ As much as fits into the ship. Unloading stops, or the ore
        would go right back. """
        if self.miner is None:
            return
        if self.depot is not None:
            self.depot.stop()
        load_ore(self.stock, self.miner.ore, mineral, self.room)
        self.refresh()

    def price(self, mineral: str) -> int:
        """ Here, for a unit """
        return ore_price(mineral, self.prices.factor(mineral))

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
            self.wallet, self.prices.factor(mineral),
        )
        self.refresh()


load_style(__file__)
