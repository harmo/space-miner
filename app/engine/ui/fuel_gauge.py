""" The fuel left in the tank, shown at the top right while flying. Styled
in fuel_gauge.kv. """

from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from ...logic.hud import fuel_color
from ...logic.ship.fuel import Tank
from .widgets import load_style


class FuelGauge(BoxLayout):

    fill = NumericProperty(1.)                 # from 0 to 1
    amount = StringProperty('')
    color = ListProperty([1., 1., 1.])


def show_fuel(gauge: FuelGauge, tank: Tank) -> None:
    gauge.fill = tank.share
    gauge.amount = f'{tank.share:.0%}'.replace('%', ' %')
    gauge.color = list(fuel_color(tank.gauge))


load_style(__file__)
