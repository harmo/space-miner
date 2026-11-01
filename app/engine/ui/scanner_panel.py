""" The scanner: what it finds within its reach, mineral by mineral, and
which minerals it looks for. Opened in flight, the game going on behind.
Styled in scanner_panel.kv. """

from collections.abc import Callable
from typing import Any

from kivy.clock import Clock, ClockEvent
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout

from ...logic.base.missions import Desk, lacking, needs_at
from ...logic.config import IMAGES
from ...logic.mining.minerals import MINED, MINERALS, asteroid_texture
from ...logic.ship.scanner import counts
from ..ship.player import Player
from ..world.solar_system import SolarSystem
from .cargo_panel import ICON_SHAPE
from .widgets import load_style

REFRESH = .5                  # seconds between scans, while open


class ScanRow(BoxLayout):
    """ Pressed, the mineral is looked for, or not anymore """
    panel = ObjectProperty(None)
    mineral = StringProperty('')
    icon = StringProperty('')
    name = StringProperty('')
    count = NumericProperty(0)
    color = ListProperty([1., 1., 1.])
    looked_for = BooleanProperty(False)

    def on_touch_down(self, touch: Any) -> bool:
        if self.collide_point(*touch.pos):
            self.panel.toggle(self.mineral)
            return True
        return False


class ScannerPanel(BoxLayout):

    open = BooleanProperty(False)
    reach = StringProperty('')
    missions = BooleanProperty(False)   # following what they lack

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.player: Player | None = None
        self.system: SolarSystem | None = None
        self.desks: Callable[[], list[Desk]] = list  # with the missions
        self.scans: ClockEvent | None = None
        self.rows: dict[str, ScanRow] = {}

    def setup(
        self,
        player: Player,
        system: SolarSystem,
        desks: Callable[[], list[Desk]]
    ) -> None:
        self.player, self.system, self.desks = player, system, desks
        rows = self.ids.rows
        rows.clear_widgets()
        for name in MINED:
            mineral = MINERALS[name]
            texture = asteroid_texture(name, ICON_SHAPE)
            self.rows[name] = row = ScanRow(
                panel=self, mineral=name, name=mineral.name,
                icon=f'{IMAGES}/asteroids/minerals/{texture}.png',
                color=list(mineral.color),
            )
            rows.add_widget(row)

    def toggle_open(self) -> None:
        self.open = not self.open

    def on_open(self, instance: Any, open: bool) -> None:
        if self.scans is not None:
            self.scans.cancel()
            self.scans = None
        if open:
            self.refresh()
            self.scans = Clock.schedule_interval(
                lambda dt: self.refresh(), REFRESH
            )

    def refresh(self) -> None:
        player, system = self.player, self.system
        if player is None or system is None:
            return
        reach = player.stats.scan
        self.reach = f'portée {round(reach):,}'.replace(',', ' ')
        found = (
            counts(system.asteroids, player.ship.position, reach)
            if player.ship is not None else dict.fromkeys(MINED, 0)
        )
        self.missions = player.scan_missions
        for name, row in self.rows.items():
            row.count = found[name]
            row.looked_for = name in player.looked_for

    def look_for(self, minerals: set[str]) -> None:
        """ Chosen by hand: missions are not followed anymore """
        if self.player is not None:
            self.player.scan_missions = False
            self.player.looked_for = minerals
            self.refresh()

    def toggle(self, mineral: str) -> None:
        if self.player is not None:
            self.look_for(self.player.looked_for ^ {mineral})

    def everything(self) -> None:
        self.look_for(set(MINED))

    def nothing(self) -> None:
        self.look_for(set())

    def for_missions(self) -> None:
        """ What the missions under way still lack, wherever they are, and
        goes on following it, see show_needs """
        if self.player is not None:
            self.player.scan_missions = True
            self.player.looked_for = lacking(
                needs_at(self.desks(), self.player.miner.ore)
            )
            self.refresh()


load_style(__file__)
