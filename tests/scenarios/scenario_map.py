""" The map of the solar system, the game standing still behind it """

from typing import Any

from .harness import Scenario

scenario = Scenario('map')
check = scenario.check
remembered: dict[str, Any] = {}


@scenario.step(1.)
def takes_off() -> None:
    remembered['touch'] = scenario.hold_towards(scenario.away_from_earth())


@scenario.step(.8)
def opens_the_map() -> None:
    remembered['touch'].touch_up()
    scenario.press(scenario.base.ids.hangar_button)


@scenario.step(.3)
def from_the_row() -> None:
    check(scenario.base.panel == '', 'the base only opens on the Earth')
    scenario.press(scenario.game.ids.map_button)
    remembered['time'] = scenario.game.time
    remembered['ship'] = scenario.player.ship.position


@scenario.step(.6)
def stands_still() -> None:
    game = scenario.game
    check(game.map_open, 'the map opens')
    check(game.time == remembered['time'], 'the game stands still')
    check(scenario.player.ship.position == remembered['ship'],
          'and the ship with it')
    check(len(game.ids.map.canvas.children) > 20, 'the map is drawn')
    scenario.screenshot('map')
    for _ in range(2):
        scenario.press(scenario.button(game.ids.map.parent, '+'))


@scenario.step(.3)
def zooms_in() -> None:
    game = scenario.game
    check(game.ids.map.zoom == 4, f'zoomed in: {game.ids.map.zoom}')
    x, y = game.ids.map.chart.place(scenario.player.ship.position)
    check(abs(x - game.center_x) < 1 and abs(y - game.center_y) < 1,
          'on the ship')
    scenario.screenshot('zoomed')
    scenario.escape()


@scenario.step(.3)
def escape_closes_it() -> None:
    check(not scenario.game.map_open, 'escape closes the map')
    check(scenario.game.time > remembered['time'], 'the game goes on')
    from kivy.core.window import Window
    Window.dispatch('on_keyboard', 109, 0, 'm', [])


@scenario.step(.3)
def m_opens_it() -> None:
    check(scenario.game.map_open, 'M opens the map')
    scenario.press(scenario.button(scenario.game.ids.map.parent, 'Fermer'))


@scenario.step(.3)
def closed() -> None:
    check(not scenario.game.map_open, 'and its button closes it')


scenario.run()
