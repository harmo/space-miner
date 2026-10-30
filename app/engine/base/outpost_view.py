""" An outpost, shown while the ship is parked on its pad: its depot and
the credits, its construction, delivered to from the cargo, and its post
serving the ship. Styled in outpost_view.kv. """

from typing import TYPE_CHECKING

from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from ...logic.base.outposts import unlocked
from ...logic.base.post import Docked
from ...logic.config import IMAGES
from ...logic.mining.minerals import MINERALS, asteroid_texture
from ...logic.mining.ore import cargo_total, whole_units
from ..ship.player import Player
from ..ui.cargo_panel import ICON_SHAPE, show_depot
from ..ui.widgets import load_style
from .missions_panel import credits_text
from .outposts import Outpost

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

    def show(self, outpost: Outpost, cargo: dict[str, float]) -> None:
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
        self.can_deliver = any(
            whole_units(cargo.get(name, 0.)) > 0 for name in needed
        )


class OutpostView(Widget):

    docked = BooleanProperty(False)     # on the pad of an outpost
    panel = StringProperty('')          # "site" or none
    shown = BooleanProperty(False)      # its buttons, with no panel open
    building = BooleanProperty(False)   # stages are left to build
    has_depot = BooleanProperty(False)
    can_unload = BooleanProperty(False)
    unloading = BooleanProperty(False)
    money = StringProperty('')

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.player: Player | None = None
        self.outposts: list[Outpost] = []
        self.base: EarthBase | None = None  # its credits
        self.current: Outpost | None = None  # where the ship is parked

    def setup(self, player: Player, outposts: list[Outpost],
              base: 'EarthBase') -> None:
        self.player, self.outposts, self.base = player, outposts, base

    @property
    def buttons(self) -> list[Widget]:
        return [self.ids.site_button, self.ids.unload_button]

    def update(self, dt: float) -> None:
        player, base = self.player, self.base
        if player is None or base is None:
            return
        ore = player.miner.ore
        self.current = None
        for outpost in self.outposts:
            served = player.docked and outpost.serves(player.parking)
            if served:
                self.current = outpost
            outpost.post.update(
                dt, Docked(ore, player.tank) if served else None,
                base.wallet,
            )
        current = self.current
        self.docked = current is not None
        if current is None:
            self.panel = ''
            return
        depot = current.post.depot
        self.building = current.construction.stage is not None
        self.has_depot = current.post.services.depot
        self.unloading = depot.unloading
        self.can_unload = (
            self.has_depot and not self.unloading and cargo_total(ore) > 0
        )
        self.money = credits_text(base.wallet.credits)
        show_depot(self.ids.depot, depot, False)

    def deliver(self) -> None:
        if self.current is None or self.player is None:
            return
        built = self.current.deliver(self.player.miner.ore)
        panel = self.ids.site
        panel.news = f'{built.name} construit' if built else ''
        panel.show(self.current, self.player.miner.ore)

    def unload(self) -> None:
        if self.current is not None and self.player is not None:
            self.current.post.depot.start(self.player.miner.ore)

    def open(self) -> None:
        if self.current is None or self.player is None:
            return
        self.ids.site.news = ''
        self.ids.site.show(self.current, self.player.miner.ore)
        self.panel = 'site'

    def close(self) -> None:
        self.panel = ''


load_style(__file__)
