""" Gauges at the top right while flying: the fuel left in the tank, and
the heat of the hull once it warms up. Styled in gauges.kv. """

from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from ...logic.hud import fuel_color, heat_color
from ...logic.ship.fuel import Tank
from ...logic.ship.heat import Hull
from .widgets import load_style


class Gauge(BoxLayout):

    title = StringProperty('')
    fill = NumericProperty(0.)                 # from 0 to 1
    amount = StringProperty('')
    color = ListProperty([1., 1., 1.])


def percent(share: float) -> str:
    return f'{share:.0%}'.replace('%', ' %')


def show_fuel(gauge: Gauge, tank: Tank) -> None:
    gauge.fill = tank.share
    gauge.amount = percent(tank.share)
    gauge.color = list(fuel_color(tank.gauge))


def show_heat(gauge: Gauge, hull: Hull) -> None:
    gauge.fill = hull.heat
    gauge.amount = percent(hull.heat)
    gauge.color = list(heat_color(hull.warmth))


load_style(__file__)
