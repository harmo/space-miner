""" An outpost, shown while the ship is parked on its pad: its depot, ore
loading back from there, and the credits, its construction, delivered to
from the cargo, its post serving the ship, and once it trades its market
and missions. Styled in outpost_view.kv. """

from typing import TYPE_CHECKING

from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from ...logic.base.outposts import Outpost
from ...logic.base.post import Post
from ...logic.base.quays import can_send
from ...logic.base.sites import unlocked
from ...logic.config import IMAGES
from ...logic.mining.minerals import MINERALS, asteroid_texture
from ...logic.mining.ore import Hold, whole_units
from ..audio import audio
from ..ship.player import Player
from ..ui.cargo_panel import ICON_SHAPE
from ..ui.widgets import load_style
from .market_panel import MarketPanel  # noqa: F401
from .missions_panel import MissionsPanel  # noqa: F401
from .post_view import PostView
from .quays import quays_of
from .shuttle_panel import ShuttlePanel  # noqa: F401

if TYPE_CHECKING:
    from .earth_base import EarthBase


class SupplyRow(BoxLayout):
    """ Of a mineral the stage being built needs """
    icon = StringProperty('')
    name = StringProperty('')
    progress = StringProperty('')       # delivered / needed
    held = StringProperty('')           # in the cargo
    met = BooleanProperty(False)


class SitePanel(BoxLayout):
    """ The construction of an outpost """
    view = ObjectProperty(None)         # the outpost view
    title = StringProperty('')
    stage = StringProperty('')
    adds = StringProperty('')           # once built
    news = StringProperty('')           # a stage just built
    can_deliver = BooleanProperty(False)

    def show(self, outpost: Outpost, cargo: Hold) -> None:
        construction = outpost.construction
        self.title = f'CHANTIER  ·  {outpost.name}'
        stage = construction.stage
        rows = self.ids.rows
        rows.clear_widgets()
        if stage is None:
            self.stage, self.adds, self.can_deliver = 'Achevé', '', False
            return
        count = len(construction.site.stages)
        self.stage = f'Étape {construction.built + 1} / {count}  ·  ' \
            f'{stage.name}'
        self.adds = 'Apportera ' + ', '.join(
            unlocked(stage, construction.services)
        )
        locked = construction.locked
        if locked and stage.permit is not None:
            permit = stage.permit.mission.client
            self.adds = f'Concession à obtenir sur Terre : {permit}'
        needed = construction.needed
        for name, units in stage.materials:
            delivered = units - needed.get(name, 0)
            texture = asteroid_texture(name, ICON_SHAPE)
            held = whole_units(cargo.get(name, 0.))
            rows.add_widget(SupplyRow(
                icon=f'{IMAGES}/asteroids/minerals/{texture}.png',
                name=MINERALS[name].name,
                progress=f'{delivered} / {units}',
                held=f'soute {held}' if held else '',
                met=name not in needed,
            ))
        self.can_deliver = not locked and any(
            whole_units(cargo.get(name, 0.)) > 0 for name in needed
        )


class OutpostView(PostView):
    """ Docked on the pad of an outpost. Its panel: "site", "market", the
    depot alone without a market, "missions" or none """

    building = BooleanProperty(False)   # stages are left to build
    has_depot = BooleanProperty(False)
    has_market = BooleanProperty(False)
    has_missions = BooleanProperty(False)
    # Where its buttons stand in the row, those shown from the left
    site_slot = NumericProperty(0)
    unload_slot = NumericProperty(0)
    market_slot = NumericProperty(0)
    missions_slot = NumericProperty(0)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.outposts: list[Outpost] = []
        self.base: EarthBase | None = None  # its credits
        self.current: Outpost | None = None  # where the ship is parked

    def setup(self, player: Player, outposts: list[Outpost],
              base: 'EarthBase') -> None:
        self.player, self.outposts, self.base = player, outposts, base

    @property
    def post(self) -> Post | None:
        return self.current.post if self.current else None

    @property
    def buttons(self) -> list[Widget]:
        ids = self.ids
        return [
            ids.site_button, ids.unload_button, ids.market_button,
            ids.missions_button,
        ]

    def update(self, dt: float) -> None:
        player, base = self.player, self.base
        if player is None or base is None:
            return
        self.current = None
        found: list[str] = []
        for outpost in self.outposts:
            served = player.docked and outpost.serves(player.parking)
            finds = outpost.post.update(
                dt, player.served if served else None, base.wallet,
            )
            if served:
                self.current, found = outpost, finds
        current = self.current
        self.docked = current is not None
        if current is None:
            self.panel = ''
            self.unloading = self.crushing = False
            return
        services = current.post.services
        self.building = current.construction.stage is not None
        self.has_depot = services.depot
        self.has_market = services.market
        self.has_missions = services.missions and current.board is not None
        self.arrange()
        self.show_post(current.post, found, current.board, base.wallet)

    def arrange(self) -> None:
        """ The buttons shown, side by side from the left of the row """
        slot = -2
        for name, shown in (
            ('site', self.building), ('unload', self.has_depot),
            ('market', self.has_depot), ('missions', self.has_missions),
        ):
            if shown:
                setattr(self, f'{name}_slot', slot)
                slot += 1

    def deliver(self) -> None:
        if self.current is None or self.player is None:
            return
        built = self.current.deliver(self.player.miner.ore)
        audio.play('built' if built else 'deliver')
        panel = self.ids.site
        panel.news = f'{built.name} construit' if built else ''
        panel.show(self.current, self.player.miner.ore)

    def open(self, panel: str) -> None:
        current, player, base = self.current, self.player, self.base
        if current is None or player is None or base is None:
            return
        ore, depot, board = player.miner.ore, current.post.depot, current.board
        if panel == 'shuttles':
            quays = quays_of(base, self.outposts)
            here = next(q for q in quays if q.key == current.key)
            self.show_dock(here, quays)
            return
        if panel == 'site':
            self.ids.site.news = ''
            self.ids.site.show(current, ore)
        elif panel == 'market':
            market = self.ids.market
            market.selling = current.post.services.market
            quays = quays_of(base, self.outposts)
            here = next(q for q in quays if q.key == current.key)
            market.shuttles = can_send(here, quays)
            market.wallet, market.stock = base.wallet, depot.stock
            market.depot, market.miner = depot, player.miner
            refinery = current.post.services.refinery
            market.board = board
            market.crusher = current.post.crusher if refinery else None
            market.prices = current.construction.site.trade
            market.refresh()
        elif board is None:
            return
        else:
            missions = self.ids.missions
            missions.board, missions.stock = board, depot.stock
            missions.cargo, missions.laser = ore, player.stats.laser
            missions.refresh()
        self.panel = panel



load_style(__file__)
