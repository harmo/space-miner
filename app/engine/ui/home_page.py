""" The home page, over the game which runs behind it, or is paused: the
three games saved, to play or erase, resuming the paused one, the settings,
and quitting on computers. Styled in home_page.kv. """

from datetime import datetime
from typing import Any

from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout

from ...logic.slots import SLOTS, SlotSummary, summary
from ..base.missions_panel import credits_text
from ..storage import read_save, saved_at
from .widgets import Layer, load_style

SAVED_AT = '%d/%m/%Y  %H:%M'


def counted(number: int, name: str) -> str:
    return f"{number} {name}{'s' if number > 1 else ''}"


def slot_text(number: int, told: SlotSummary | None, saved: float) -> str:
    """ What its button tells """
    title = f'Partie {number}'
    if told is None:
        return f'{title}\nNouvelle partie'
    return '\n'.join((
        title,
        f"{credits_text(told.credits)}  ·  "
        f"{counted(told.missions, 'mission')}",
        f"{counted(told.outposts, 'base')}  ·  "
        f"{datetime.fromtimestamp(saved).strftime(SAVED_AT)}",
    ))


class SlotCard(BoxLayout):
    home = ObjectProperty(None)
    slot = NumericProperty(1)
    text = StringProperty('')
    filled = BooleanProperty(False)     # a game saved there
    current = BooleanProperty(False)    # the paused game
    confirming = BooleanProperty(False)     # erasing it, once asked


class HomePage(Layer):

    compact = BooleanProperty(False)        # tighter, as on phones
    paused = BooleanProperty(False)         # a game to resume
    mobile = BooleanProperty(False)         # apps closed from the system
    settings_open = BooleanProperty(False)  # over it, hiding it

    __events__ = ('on_play', 'on_slot', 'on_erase', 'on_settings')

    def on_kv_post(self, base_widget: Any) -> None:
        for number in range(1, SLOTS + 1):
            self.ids.slots.add_widget(SlotCard(home=self, slot=number))

    def on_play(self) -> None:
        """ Resuming the paused game """

    def on_slot(self, slot: int) -> None:
        """ Playing the game saved there """

    def on_erase(self, slot: int) -> None:
        """ Its game was erased, once confirmed """

    def on_settings(self) -> None:
        """ Opening them """

    def refresh(self, current: int | None) -> None:
        """ What is saved now, `current` being the paused game """
        for card in self.ids.slots.children:
            save = read_save(card.slot)
            card.filled = save is not None
            card.current = card.slot == current
            card.confirming = False
            card.text = slot_text(
                card.slot, summary(save) if save else None,
                saved_at(card.slot),
            )

    def erase(self, card: SlotCard) -> None:
        if card.confirming:
            self.dispatch('on_erase', card.slot)
        else:
            card.confirming = True


load_style(__file__)
