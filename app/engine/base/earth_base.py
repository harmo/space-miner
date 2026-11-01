""" The base on the Earth, open while the ship is landed there. Its post
fills the tank, takes the cargo into its depot and crushes rock, see
post.py. The base keeps what the whole game shares: the credits, the
hangar where the ship is refitted, and the missions. It tows ships out of
fuel back. Styled in earth_base.kv. """

from random import Random

from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.widget import Widget

from ...logic.base.board import Board
from ...logic.base.crushing import Crusher
from ...logic.base.outposts import Outpost
from ...logic.base.permits import Permits
from ...logic.base.post import Post, home_post
from ...logic.base.quays import can_send
from ...logic.base.refuel import tow, tow_price
from ...logic.base.reputation import tier
from ...logic.base.shop import Inventory
from ...logic.base.unloading import Depot
from ...logic.base.wallet import Wallet
from ...logic.ship.ground import surface_distance
from ..ship.player import Player
from ..ui.widgets import (
    PanelButton,  # noqa: F401
    load_style,
)
from .hangar import HangarPanel  # noqa: F401
from .market_panel import MarketPanel  # noqa: F401
from .missions_panel import MissionsPanel, credits_text  # noqa: F401
from .post_view import PostView
from .quays import quays_of
from .shuttle_panel import ShuttlePanel  # noqa: F401


class EarthBase(PostView):
    """ Its panel: "market", "missions", "hangar" or none """

    new_parts = BooleanProperty(False)  # a tier reached, not seen yet
    stranded = BooleanProperty(False)   # the ship, out of fuel
    tow_cost = StringProperty('')

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.wallet = Wallet()
        self.inventory = Inventory()        # parts in the hangar
        self.permits = Permits()            # shared with the outposts
        self.outposts: list[Outpost] = []
        self.rng = Random()
        self.home = home_post(self.rng)
        self.board: Board | None = None
        self.seen_tier = 1                  # in the hangar

    def setup(self, player: Player, rng: Random) -> None:
        self.player, self.rng = player, rng
        self.home = home_post(rng)
        self.connect()

    def reset(self) -> None:
        """ For a new game """
        self.wallet = Wallet()
        self.inventory = Inventory()
        self.permits.granted.clear()
        self.permits.followed.clear()
        self.home = home_post(self.rng)
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
        market.crusher, market.depot = self.crusher, self.depot
        self.ids.missions.board = self.board
        self.ids.missions.permits = self.permits
        self.ids.missions.stock = stock
        if player is not None:
            self.ids.missions.cargo = player.miner.ore
            market.miner = player.miner

    @property
    def post(self) -> Post:
        return self.home

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
        self.docked = player.docked_on(player.system.earth)
        self.stranded = player.stranded
        if self.stranded:
            self.tow_cost = credits_text(self.tow_price)
        found = self.home.update(
            dt, player.served if self.docked else None, self.wallet,
        )
        self.show_post(self.home, found, self.board, self.wallet)
        if not self.docked:
            self.panel = ''
        self.new_parts = tier(self.board.validated) > self.seen_tier

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

    def open(self, panel: str) -> None:
        if self.player is None or not self.player.docked:
            return
        if panel == 'shuttles':
            quays = quays_of(self, self.outposts)
            self.show_dock(quays[0], quays)
            return
        if panel == 'hangar':
            self.ids.hangar.open()
            if self.board is not None:
                self.seen_tier = tier(self.board.validated)
        elif panel == 'market':
            quays = quays_of(self, self.outposts)
            self.ids.market.shuttles = can_send(quays[0], quays)
            self.ids.market.refresh()
        else:
            self.ids.missions.laser = self.player.stats.laser
            self.ids.missions.refresh()
        self.panel = panel


load_style(__file__)
