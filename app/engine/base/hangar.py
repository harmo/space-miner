""" The hangar on the Earth: hulls and parts are bought, parts are fitted
on the ship, taken off and sold back, and the ship moves onto other
hulls. A slot is picked, or the hull, then one of what fits it, which
shows how the ship would change. Styled in hangar.kv. """

from typing import Any

from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from ...logic.base.missions import Board
from ...logic.base.reputation import is_sold, next_tier
from ...logic.base.shop import Inventory, buy, buy_hull, refit, rehull, sell
from ...logic.base.wallet import Wallet
from ...logic.mining.ore import Hold, cargo_load
from ...logic.ship.hulls import HULLS
from ...logic.ship.parts import PARTS
from ...logic.ship.shipyard import (
    Design,
    fitted,
    options,
    ship_stats,
    transfer,
)
from ..ship.player import Player
from ..ship.ship_textures import ship_preview
from ..ui.widgets import load_style
from .hangar_rows import (
    PartRow,
    SlotButton,
    StatRow,
    hull_row,
    part_row,
    stat_rows,
)
from .missions_panel import credits_text

HULL = 'hull'                 # picked instead of a slot, to change hulls


class HangarPanel(BoxLayout):

    hull = StringProperty('')
    preview = ObjectProperty(None, allownone=True)   # texture of the ship
    slot_name = StringProperty('')
    money = StringProperty('')
    message = StringProperty('')
    fitting = BooleanProperty(False)    # the chosen part isn't the fitted one
    teaser = StringProperty('')         # parts of the next tier

    def __init__(self, **kwargs: Any) -> None:
        self.register_event_type('on_close')
        super().__init__(**kwargs)
        self.player: Player | None = None
        self.inventory = Inventory()
        self.wallet = Wallet()
        self.stock: Hold = {}   # of the depot
        self.board: Board | None = None     # its missions make reputation
        self.slot = ''                      # or HULL
        # Part, or hull, compared with the ship as it is
        self.chosen: str | None = None

    def on_close(self) -> None:
        """ The close button was pressed """

    @property
    def design(self) -> Design:
        return self.player.design if self.player else Design()

    @property
    def load(self) -> float:
        return cargo_load(self.player.miner.ore) if self.player else 0.

    def open(self) -> None:
        self.message = ''
        slots = HULLS[self.design.hull].slots
        if self.slot not in slots and self.slot != HULL:
            self.slot = next(iter(slots))
        self.pick_slot(self.slot)

    def pick_slot(self, slot_id: str) -> None:
        self.slot = slot_id
        if slot_id == HULL:
            self.chosen = self.design.hull
        else:
            self.chosen = self.design.parts.get(slot_id)
        self.refresh()

    def choose(self, part_id: str | None) -> None:
        """ Compare the ship with this part """
        self.chosen = part_id
        self.message = ''
        self.refresh()

    def fit(self, part_id: str | None) -> None:
        """ Or move onto the hull """
        if self.player is None:
            return
        if self.slot == HULL and part_id is not None:
            design = rehull(self.design, part_id, self.inventory, self.load)
        else:
            design = refit(
                self.design, self.slot, part_id, self.inventory, self.load
            )
        if design is None:
            self.message = 'La soute contient trop de minerai'
        else:
            self.player.refit(design)
            self.chosen = part_id
        self.refresh()

    def buy(self, item: str) -> None:
        """ Fitted right away, the part there goes to the hangar. A hull
        takes the ship at once, with its parts. """
        buying = buy_hull if self.slot == HULL else buy
        if buying(item, self.wallet, self.stock, self.inventory):
            self.fit(item)

    def sell(self, part_id: str) -> None:
        sell(part_id, self.wallet, self.inventory)
        self.refresh()

    def refresh(self) -> None:
        design, hull = self.design, HULLS[self.design.hull]
        self.hull = hull.name
        self.money = credits_text(self.wallet.credits)
        if self.slot == HULL:
            self.slot_name = 'COQUE'
            candidate = transfer(design, self.chosen or design.hull)[0]
        else:
            self.slot_name = hull.slots[self.slot].name.upper()
            candidate = fitted(design, self.slot, self.chosen)
        stats = ship_stats(candidate)
        self.preview = ship_preview(candidate, stats.size)
        self.fitting = candidate != design
        self.ids.stats.clear_widgets()
        for row in stat_rows(ship_stats(design), stats):
            self.ids.stats.add_widget(row)
        self.ids.slots.clear_widgets()
        self.ids.slots.add_widget(SlotButton(
            panel=self, slot=HULL, name='Coque', part=hull.name,
            selected=self.slot == HULL,
        ))
        for slot_id, slot in hull.slots.items():
            self.ids.slots.add_widget(SlotButton(
                panel=self, slot=slot_id, name=slot.name,
                part=PARTS[part].name if (part := design.parts.get(slot_id))
                else 'Vide',
                selected=slot_id == self.slot,
            ))
        self.ids.parts.clear_widgets()
        if self.slot == HULL:
            for hull_id in self.shown_hulls():
                self.ids.parts.add_widget(hull_row(
                    self, hull_id, design, self.chosen, self.load,
                ))
        else:
            for part_id in self.shown_options():
                self.ids.parts.add_widget(part_row(
                    self, part_id, design, self.slot, self.chosen, self.load,
                ))
        self.teaser = self.coming()

    @property
    def validated(self) -> int:
        return self.board.validated if self.board else 0

    def shown_options(self) -> list[str | None]:
        """ Those sold at this reputation, and those the player has """
        fitted_part = self.design.parts.get(self.slot)
        return [
            part_id for part_id in options(self.design, self.slot)
            if part_id is None or part_id == fitted_part
            or self.inventory.count(part_id)
            or is_sold(PARTS[part_id], self.validated)
        ]

    def shown_hulls(self) -> list[str]:
        return [
            hull_id for hull_id, hull in HULLS.items()
            if hull_id in self.inventory.hulls
            or is_sold(hull, self.validated)
        ]

    def coming(self) -> str:
        """ What the next tier brings for this slot, or the hull, and
        when """
        coming = next_tier(self.validated)
        if coming is None:
            return ''
        level, needed = coming
        if self.slot == HULL:
            count = sum(hull.tier == level for hull in HULLS.values())
            what = 'coque' if count == 1 else 'coques'
        else:
            count = sum(
                PARTS[part_id].tier == level
                for part_id in options(self.design, self.slot) if part_id
            )
            what = 'pièce' if count == 1 else 'pièces'
        if not count:
            return ''
        return (
            f'+{count} {what} au palier {level} :  '
            f'{self.validated} / {needed} missions validées'
        )


__all__ = ['HangarPanel', 'PartRow', 'SlotButton', 'StatRow']


load_style(__file__)
