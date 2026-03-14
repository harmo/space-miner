""" Widgets of the interface, styled in widgets.kv along with what the
panels share. Each panel has its own kv file, next to its module. """

from pathlib import Path

from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.widget import Widget


class PanelButton(Button):
    """ Rounded button in the style of the panels, with an outline as bright
    as its glow """

    glow = NumericProperty(.3)        # opacity of the outline
    corner = NumericProperty(12)      # radius of the corners, in dp

    def on_touch_down(self, touch: MotionEvent) -> bool:
        """ Disabled, it lets touches through to what lies below, as hidden
        buttons are """
        return not self.disabled and bool(super().on_touch_down(touch))


class Layer(Widget):
    """ Widgets shown or hidden together. Hidden, the layer is invisible and
    lets touches through, where a disabled widget would swallow them. """

    shown = BooleanProperty(True)

    def on_shown(self, instance: Widget, shown: bool) -> None:
        self.opacity = 1. if shown else 0.

    def on_touch_down(self, touch: MotionEvent) -> bool:
        return self.shown and bool(super().on_touch_down(touch))

    def on_touch_move(self, touch: MotionEvent) -> bool:
        return self.shown and bool(super().on_touch_move(touch))

    def on_touch_up(self, touch: MotionEvent) -> bool:
        return self.shown and bool(super().on_touch_up(touch))


def load_style(module: str) -> None:
    """ The kv file next to a module, named after it. The shared style is
    loaded first, along with this module. """
    Builder.load_file(str(Path(module).with_suffix('.kv')))


load_style(__file__)
