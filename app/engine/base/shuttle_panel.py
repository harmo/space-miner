""" The dock of a post: where its shuttle goes, and what it carries. Styled
in shuttle_panel.kv. """

from typing import Any

from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from ...logic.base.quays import Quay, destination_of
from ...logic.base.shuttles import Route
from ...logic.mining.minerals import MINERALS
from ...logic.mining.ore import whole_units
from ..ui.widgets import PanelButton, load_style


class ChoiceButton(PanelButton):
    panel = ObjectProperty(None)
    key = StringProperty('')            # of a post, or a mineral
    place = BooleanProperty(False)      # a post
    chosen = BooleanProperty(False)


class ShuttlePanel(BoxLayout):

    title = StringProperty('')
    status = StringProperty('')

    def __init__(self, **kwargs: Any) -> None:
        self.register_event_type('on_close')
        super().__init__(**kwargs)
        self.quay: Quay | None = None
        self.quays: list[Quay] = []
        self.destination = ''
        self.minerals: list[str] = []

    def on_close(self) -> None:
        """ The close button was pressed """

    def show(self, quay: Quay, quays: list[Quay]) -> None:
        self.quay, self.quays = quay, quays
        route = quay.post.shuttle.route
        self.destination = route.destination if route else ''
        self.minerals = list(route.minerals) if route else []
        self.refresh()

    def refresh(self) -> None:
        quay = self.quay
        if quay is None:
            return
        self.title = f'NAVETTES  ·  {quay.name}'
        places = self.ids.places
        places.clear_widgets()
        for other in self.quays:
            if other is not quay and other.takes:
                places.add_widget(ChoiceButton(
                    panel=self, key=other.key, text=other.name, place=True,
                    chosen=other.key == self.destination,
                ))
        minerals = self.ids.minerals
        minerals.clear_widgets()
        stock = quay.post.depot.stock
        for name, mineral in MINERALS.items():
            if whole_units(stock.get(name, 0.)) > 0 or name in self.minerals:
                minerals.add_widget(ChoiceButton(
                    panel=self, key=name, text=mineral.name,
                    chosen=name in self.minerals,
                ))
        self.follow()

    def choose(self, button: ChoiceButton) -> None:
        key = button.key
        if button.place:
            self.destination = '' if key == self.destination else key
        elif key in self.minerals:
            self.minerals.remove(key)
        else:
            self.minerals.append(key)
        if self.quay is not None:
            self.quay.post.shuttle.route = (
                Route(self.destination, tuple(self.minerals))
                if self.destination and self.minerals else None
            )
        self.refresh()

    def follow(self) -> None:
        """ Where the shuttle is """
        quay = self.quay
        if quay is None:
            return
        shuttle = quay.post.shuttle
        target = destination_of(quay, self.quays)
        left = round(shuttle.left)
        if shuttle.route is None or target is None:
            self.status = 'Choisissez une destination et des ressources'
        elif shuttle.leg == 'out':
            self.status = f'En route vers {target.name}  ·  {left} s'
        elif shuttle.leg == 'back':
            self.status = f'Au retour  ·  {left} s'
        else:
            self.status = 'À quai, en attente de ressources'


load_style(__file__)
