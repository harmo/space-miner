""" The base on the Earth, open while the ship is landed there. Its post
fills the tank, takes the cargo into its depot and crushes rock, see
post.py. The base keeps what the whole game shares: the credits, the
hangar where the ship is refitted, and the missions. It tows ships out of
fuel back. Styled in earth_base.kv. """

from random import Random

from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.widget import Widget

from ...logic.base.crushing import Crusher
from ...logic.base.missions import Board
from ...logic.base.post import EVERYTHING, Docked, Post
from ...logic.base.refuel import tow, tow_price
from ...logic.base.reputation import tier
from ...logic.base.shop import Inventory
from ...logic.base.unloading import Depot
from ...logic.base.wallet import Wallet
from ...logic.mining.ore import cargo_total
from ...logic.ship.landing import surface_distance
from ..ship.player import Player
from ..ui.cargo_panel import show_depot
from ..ui.widgets import (
    PanelButton,  # noqa: F401
    load_style,
)
from .hangar import HangarPanel  # noqa: F401
from .market_panel import MarketPanel  # noqa: F401
from .missions_panel import MissionsPanel, credits_text  # noqa: F401


class EarthBase(Widget):

    docked = BooleanProperty(False)
    # Open: "market", "missions", "hangar" or none
    panel = StringProperty('')
    shown = BooleanProperty(False)      # its buttons, with no panel open
    can_unload = BooleanProperty(False)
    unloading = BooleanProperty(False)
    crushing = BooleanProperty(False)   # rock, at the refinery
    money = StringProperty('')
    to_validate = BooleanProperty(False)  # a mission can be validated
    new_parts = BooleanProperty(False)  # a tier reached, not seen yet
    full_row = BooleanProperty(False)   # the scanner button ends its row
    stranded = BooleanProperty(False)   # the ship, out of fuel
    tow_cost = StringProperty('')

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.wallet = Wallet()
        self.inventory = Inventory()        # parts in the hangar
        self.player: Player | None = None
        self.rng = Random()
        self.home = Post('Terre', EVERYTHING, self.rng)
        self.board: Board | None = None
        self.seen_tier = 1                  # in the hangar

    def setup(self, player: Player, rng: Random) -> None:
        self.player, self.rng = player, rng
        self.home = Post('Terre', EVERYTHING, rng)
        self.connect()

    def reset(self) -> None:
        """ For a new game """
        self.wallet = Wallet()
        self.inventory = Inventory()
        self.home = Post('Terre', EVERYTHING, self.rng)
        self.seen_tier = 1
        self.panel = ''
        self.connect()

    def connect(self) -> None:
        """ The panels to what they show """
        player = self.player
        self.board = Board(self.rng, self.wallet)
        stock = self.depot.stock
        hangar = self.ids.hangar
        hangar.player, hangar.inventory = player, self.inventory
        hangar.wallet, hangar.stock = self.wallet, stock
        hangar.board = self.board
        market = self.ids.market
        market.wallet, market.stock, market.board = (
            self.wallet, stock, self.board
        )
        market.crusher = self.crusher
        self.ids.missions.board = self.board
        self.ids.missions.stock = stock
        if player is not None:
            self.ids.missions.cargo = player.miner.ore

    @property
    def depot(self) -> Depot:
        return self.home.depot

    @property
    def crusher(self) -> Crusher:
        return self.home.crusher

    @property
    def buttons(self) -> list[Widget]:
        ids = self.ids
        return [
            ids.unload_button, ids.market_button, ids.missions_button,
            ids.hangar_button,
        ]

    def update(self, dt: float) -> None:
        if self.player is None or self.board is None:
            return
        player = self.player
        ore, stock = player.miner.ore, self.depot.stock
        self.docked = player.docked_on(player.system.earth)
        self.stranded = player.stranded
        if self.stranded:
            self.tow_cost = credits_text(self.tow_price)
        found = self.home.update(
            dt, Docked(ore, player.tank, player.hull) if self.docked else None,
            self.wallet,
        )
        # The market shows what was found, and when it is over
        if self.panel == 'market' and (
            found or self.crushing != self.crusher.crushing
        ):
            self.ids.market.refresh()
        self.crushing = self.crusher.crushing
        if not self.docked:
            self.panel = ''
        self.unloading = self.depot.unloading
        self.can_unload = (
            self.docked and not self.unloading and cargo_total(ore) > 0
        )
        self.money = credits_text(self.wallet.credits)
        self.to_validate = any(
            mission.can_validate(stock) for mission in self.board.active
        )
        self.new_parts = tier(self.board.validated) > self.seen_tier
        if self.docked:
            show_depot(self.ids.depot, self.depot, self.crushing)

    @property
    def tow_price(self) -> int:
        """ From where the ship is """
        ship = self.player.ship if self.player else None
        if ship is None or self.player is None:
            return 0
        return tow_price(surface_distance(
            ship.position, self.player.system.earth,
        ))

    def call_for_help(self) -> None:
        """ Towed back onto the Earth, with its cargo """
        player = self.player
        if player is not None and player.stranded:
            tow(self.tow_price, self.wallet)
            player.restart(player.design)

    def unload(self) -> None:
        if self.player is not None and self.player.docked:
            self.depot.start(self.player.miner.ore)

    def open(self, panel: str) -> None:
        if self.player is None or not self.player.docked:
            return
        if panel == 'hangar':
            self.ids.hangar.open()
            if self.board is not None:
                self.seen_tier = tier(self.board.validated)
        elif panel == 'market':
            self.ids.market.refresh()
        else:
            self.ids.missions.laser = self.player.stats.laser
            self.ids.missions.refresh()
        self.panel = panel

    def close(self) -> None:
        self.panel = ''

    def on_panel(self, instance: Widget, panel: str) -> None:
        self.ids.missions.watch(panel == 'missions')


load_style(__file__)
