""" What the views of the posts share, the Earth and outposts: what they
tell of the post the ship is landed at, and their panels """

from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.widget import Widget

from ...logic.base.board import Board
from ...logic.base.post import Post
from ...logic.base.quays import Quay
from ...logic.base.wallet import Wallet
from ..ship.player import Player
from ..ui.cargo_panel import show_depot
from .missions_panel import credits_text


class PostView(Widget):

    docked = BooleanProperty(False)     # the ship, at this post
    panel = StringProperty('')          # open, or none
    shown = BooleanProperty(False)      # its buttons, with no panel open
    can_unload = BooleanProperty(False)
    depot_full = BooleanProperty(False)
    unloading = BooleanProperty(False)
    crushing = BooleanProperty(False)   # rock, at the refinery
    to_validate = BooleanProperty(False)  # a mission can be validated
    money = StringProperty('')
    full_row = BooleanProperty(False)   # the scanner button ends its row

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.player: Player | None = None

    @property
    def post(self) -> Post | None:
        """ The one shown """
        return None

    def show_post(self, post: Post, found: list[str], board: Board | None,
                  wallet: Wallet) -> None:
        """ What it tells now, `found` being what its refinery just found.
        The market shows that, and when it is over. """
        if self.player is None:
            return
        status = post.status(self.player.miner.ore, board)
        if self.panel == 'shuttles':
            self.ids.shuttles.follow()
        if self.panel == 'market' and (
            found or self.crushing != status.crushing
        ):
            self.ids.market.refresh()
        self.crushing = status.crushing
        self.unloading = status.unloading
        self.can_unload = self.docked and status.can_unload
        self.to_validate = status.to_validate
        self.depot_full = status.full
        self.money = credits_text(wallet.credits)
        if self.docked:
            show_depot(self.ids.depot, post.depot, status.crushing)

    def unload(self) -> None:
        if self.post is not None and self.player is not None:
            self.post.depot.start(self.player.miner.ore)

    def show_dock(self, quay: Quay, quays: list[Quay]) -> None:
        """ Where its shuttle goes """
        self.ids.shuttles.show(quay, quays)
        self.panel = 'shuttles'

    def close(self) -> None:
        self.panel = ''

    def on_panel(self, instance: Widget, panel: str) -> None:
        self.ids.missions.watch(panel == 'missions')
