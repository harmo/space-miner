""" What the missions under way still need, shown while flying under the
cargo. Styled in tracker.kv. """

from kivy.properties import (
    BooleanProperty,
    ListProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout

from ...logic.base.missions import Desk, Need, needs_at
from ...logic.config import IMAGES
from ...logic.mining.minerals import MINERALS, asteroid_texture
from ..ship.player import Player
from .cargo_panel import ICON_SHAPE
from .widgets import load_style


class NeedRow(BoxLayout):
    icon = StringProperty('')
    name = StringProperty('')
    progress = StringProperty('')       # held / wanted
    color = ListProperty([1., 1., 1.])
    met = BooleanProperty(False)
    laser = StringProperty('')          # needed, when the ship's is weaker


class MissionTracker(BoxLayout):

    shown = BooleanProperty(False)      # some mission is under way

    def show(self, needs: list[Need], laser: int) -> None:
        self.shown = bool(needs)
        rows = self.ids.rows
        if len(rows.children) != len(needs):
            rows.clear_widgets()
            for _ in needs:
                rows.add_widget(NeedRow())
        for row, need in zip(reversed(rows.children), needs, strict=True):
            mineral = MINERALS[need.mineral]
            texture = asteroid_texture(need.mineral, ICON_SHAPE)
            row.icon = f'{IMAGES}/asteroids/minerals/{texture}.png'
            row.name = mineral.name
            row.progress = f'{min(need.held, need.wanted)} / {need.wanted}'
            row.color = list(mineral.color)
            row.met = need.met
            too_weak = mineral.laser > laser and not need.met
            row.laser = str(mineral.laser) if too_weak else ''


def show_needs(tracker: MissionTracker, desks: list[Desk],
               player: Player) -> None:
    """ Of the missions under way wherever they are """
    tracker.show(needs_at(desks, player.miner.ore), player.stats.laser)


load_style(__file__)
