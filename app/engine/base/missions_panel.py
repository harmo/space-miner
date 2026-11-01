""" The missions of the base: offers to accept, and accepted ones to
validate once the depot holds the ore. Styled in missions_panel.kv. """

import math
from typing import Any

from kivy.clock import Clock, ClockEvent
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout

from ...logic.base.board import Board
from ...logic.base.config import TIER_MISSIONS
from ...logic.base.missions import Mission, held
from ...logic.base.permits import Permit, Permits
from ...logic.base.reputation import next_tier, tier
from ...logic.base.sites import PERMITS
from ...logic.mining.minerals import MINERALS
from ...logic.mining.ore import Hold
from ..ui.widgets import PanelButton, load_style


def credits_text(money: int) -> str:
    return f'{money:,} cr'.replace(',', ' ')


def offer_text(mission: Mission, laser: int) -> str:
    """ What is wanted, and the laser it takes when better than the ship's
    one """
    parts = []
    for name, units in mission.wanted.items():
        mineral = MINERALS[name]
        needs = f' (laser {mineral.laser})' if mineral.laser > laser else ''
        parts.append(f'{units} {mineral.name}{needs}')
    return ' · '.join(parts)


def progress_text(mission: Mission, *holds: Hold) -> str:
    """ Units in the holds out of those wanted """
    return ' · '.join(
        f'{MINERALS[name].name} {min(units, held(name, holds))}/{units}'
        for name, units in mission.wanted.items()
    )


def coming_text(seconds: float) -> str:
    minutes, left = divmod(math.ceil(seconds), 60)
    return f'Prochaine mission dans {minutes}:{left:02d}'


def reputation_text(validated: int) -> str:
    """ The tier reached, and what the next one takes """
    text = f'Réputation : palier {tier(validated)}'
    coming = next_tier(validated)
    if coming is not None:
        level, needed = coming
        text += f'  ·  palier {level} à {needed} missions ({validated})'
    return text


WATCH = .5                    # seconds between looks at the ore


class LevelButton(PanelButton):
    panel = ObjectProperty(None)
    level = NumericProperty(1)
    chosen = BooleanProperty(False)
    reached = BooleanProperty(False)    # by the reputation


class MissionCard(BoxLayout):
    panel = ObjectProperty(None)
    client = StringProperty('')
    wanted = StringProperty('')
    reward = StringProperty('')
    action = StringProperty('')         # "Accepter" or "Valider"
    can_act = BooleanProperty(False)
    accepted = BooleanProperty(False)   # can be abandoned

    def __init__(self, mission: Mission, permit: Permit | None = None,
                 **kwargs: Any) -> None:
        self.mission = mission
        self.permit = permit    # the concession it stands for
        super().__init__(**kwargs)


class MissionsPanel(BoxLayout):

    money = StringProperty('')
    accepted = StringProperty('')       # how many, out of how many
    reputation = StringProperty('')
    coming = StringProperty('')         # the next offer, if one is due

    def __init__(self, **kwargs: Any) -> None:
        self.register_event_type('on_close')
        super().__init__(**kwargs)
        self.board: Board | None = None
        self.permits: Permits | None = None  # given here, on the Earth
        self.stock: Hold = {}   # of the depot
        self.cargo: Hold = {}   # of the ship, taken after it
        self.laser = 1                      # of the ship
        self.watching: ClockEvent | None = None

    def on_close(self) -> None:
        """ The close button was pressed """

    def watch(self, open: bool) -> None:
        """ While open, the ore keeps coming: unloaded, or sold """
        if self.watching is not None:
            self.watching.cancel()
            self.watching = None
        if open:
            self.refresh()
            self.watching = Clock.schedule_interval(
                lambda dt: self.follow(), WATCH
            )

    def follow(self) -> None:
        """ What the missions under way have, without making the cards
        anew under a finger, unless an offer came """
        board = self.board
        if board is not None and len(board.offers) != len(
            self.ids.offers.children
        ):
            self.refresh()
            return
        self.show_coming()
        for card in [*self.ids.active.children, *self.ids.permits.children]:
            card.wanted = progress_text(card.mission, self.stock, self.cargo)
            card.can_act = card.mission.can_validate(self.stock, self.cargo)

    def show_coming(self) -> None:
        left = self.board.next_offer if self.board else None
        self.coming = '' if left is None else coming_text(left)

    def refresh(self) -> None:
        board = self.board
        if board is None:
            return
        self.money = credits_text(board.wallet.credits)
        self.accepted = f'{len(board.active)}/{board.most}'
        self.reputation = reputation_text(board.validated)
        self.show_levels(board)
        self.show_coming()
        offers, active = self.ids.offers, self.ids.active
        self.show_permits(board)
        offers.clear_widgets()
        for mission in board.offers:
            offers.add_widget(MissionCard(
                mission, panel=self, client=mission.client,
                wanted=offer_text(mission, self.laser),
                reward=credits_text(mission.reward), action='Accepter',
                can_act=not board.full,
            ))
        active.clear_widgets()
        for mission in board.active:
            active.add_widget(MissionCard(
                mission, panel=self, client=mission.client,
                wanted=progress_text(mission, self.stock, self.cargo),
                reward=credits_text(mission.reward), action='Valider',
                can_act=mission.can_validate(self.stock, self.cargo),
                accepted=True,
            ))
        self.ids.none.opacity = 0 if board.active else 1

    def show_permits(self, board: Board) -> None:
        cards = self.ids.permits
        cards.clear_widgets()
        if self.permits is None:
            return
        for permit in self.permits.offered(PERMITS, board.tier):
            mission = permit.mission
            cards.add_widget(MissionCard(
                mission, permit, panel=self, client=mission.client,
                wanted=progress_text(mission, self.stock, self.cargo),
                reward=credits_text(mission.reward), action='Valider',
                can_act=mission.can_validate(self.stock, self.cargo),
            ))

    def show_levels(self, board: Board) -> None:
        levels = self.ids.levels
        buttons = [w for w in levels.children if isinstance(w, LevelButton)]
        if not buttons:
            for level in range(1, len(TIER_MISSIONS) + 1):
                levels.add_widget(LevelButton(panel=self, level=level))
            buttons = [
                w for w in levels.children if isinstance(w, LevelButton)
            ]
        for button in buttons:
            button.chosen = button.level == board.level
            button.reached = button.level <= board.tier

    def choose(self, level: int) -> None:
        """ The offers of that level """
        if self.board is not None:
            self.board.choose_level(level)
            self.refresh()

    def act(self, card: MissionCard) -> None:
        if self.board is None:
            return
        if card.permit is not None and self.permits is not None:
            self.permits.validate(
                card.permit, self.board, self.stock, self.cargo,
            )
        elif card.accepted:
            self.board.validate(card.mission, self.stock, self.cargo)
        else:
            self.board.accept(card.mission)
        self.refresh()

    def abandon(self, card: MissionCard) -> None:
        if self.board is not None:
            self.board.abandon(card.mission)
            self.refresh()


load_style(__file__)
