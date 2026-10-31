""" A scanner bought, finding asteroids, the minerals it looks for picked
in its menu """

import math
from typing import Any

from app.logic.ship.parts import PARTS
from app.logic.ship.scanner import counts, mineral_name

from .harness import Scenario

scenario = Scenario('scanner')
check = scenario.check
REACH = PARTS['scanner'].scan
remembered: dict[str, Any] = {}


def panel() -> Any:
    return scenario.game.ids.scanner


def hangar() -> Any:
    return scenario.base.ids.hangar


@scenario.step(1.)
def no_scanner_yet() -> None:
    base = scenario.base
    check(not scenario.game.scanning, 'no scanner on a new ship')
    check(scenario.game.ids.scanner_button.opacity == 0, 'nor its button')
    row = (base.ids.unload_button.x + scenario.game.ids.map_button.right) / 2
    check(abs(row - scenario.game.center_x) < 1, 'the row stays centered')
    base.wallet.earn(PARTS['scanner'].price)
    scenario.press(base.ids.hangar_button)


@scenario.step(.4)
def picks_the_internal_slot() -> None:
    check(scenario.base.ids.depot.opacity == 1,
          'the depot stays in view with the hangar open')
    scenario.screenshot('hangar')
    slot = next(
        button for button in hangar().ids.slots.children
        if button.slot == 'internal'
    )
    hangar().ids.slots.parent.scroll_to(slot, animate=False)
    remembered['slot'] = slot


@scenario.step(.3)
def buys_a_scanner() -> None:
    scenario.press(remembered['slot'].children[0])


@scenario.step(.3)
def bought() -> None:
    row = next(r for r in hangar().ids.parts.children if r.part == 'scanner')
    scenario.press(scenario.button(row, 'Acheter'))


@scenario.step(.3)
def reaches_farther() -> None:
    check(scenario.player.design.parts.get('internal') == 'scanner',
          'the scanner is fitted')
    check(scenario.player.stats.scan == REACH, 'it reaches farther')
    check(scenario.player.stats.size == (26., 16.), 'and does not show')
    stats = {row.name: row.value for row in hangar().ids.stats.children}
    check(stats['Scanner'] == f'{REACH:,.0f}'.replace(',', ' '),
          f'the hangar shows its reach: {stats["Scanner"]}')
    scenario.escape()


@scenario.step(.3)
def ends_the_row_of_buttons() -> None:
    scanner, hangar_button = (
        scenario.game.ids.scanner_button, scenario.base.ids.hangar_button,
    )
    check(scanner.opacity == 1, 'the scanner button shows')
    map_button = scenario.game.ids.map_button
    check(scanner.y == hangar_button.y
          and hangar_button.right < scanner.x < map_button.x,
          'between the hangar and the map, at the bottom')
    scenario.screenshot('row')
    scenario.press(scanner)


@scenario.step(.3)
def one_panel_at_a_time() -> None:
    check(panel().open, 'the scanner opens on the Earth too')
    scenario.press(scenario.base.ids.hangar_button)


@scenario.step(.3)
def closed_by_the_hangar() -> None:
    check(not panel().open, 'one panel at a time')
    scenario.escape()


@scenario.step(.3)
def flies_near_asteroids() -> None:
    system = scenario.game.system
    # Far from the Earth, not to land on it
    asteroid = max(
        system.asteroids,
        key=lambda rock: math.dist(rock.pos, system.earth.pos),
    )
    remembered['asteroid'] = asteroid
    x, y = asteroid.pos
    scenario.put_ship((x + 900, y), asteroid.velocity)
    scenario.press(scenario.game.ids.scanner_button)


@scenario.step(.8)
def counts_them() -> None:
    scenario.screenshot('menu')
    check(panel().open, 'the scanner opens')
    check(not scenario.base.docked, 'flying')
    check(panel().reach == f'portée {REACH:,.0f}'.replace(',', ' '),
          f'with its reach: {panel().reach}')
    expected = counts(
        scenario.game.system.asteroids, scenario.player.ship.position, REACH
    )
    shown = {name: row.count for name, row in panel().rows.items()}
    check(shown == expected, 'counting what is within reach')
    scenario.press(scenario.button(panel(), 'Aucun'))


@scenario.step(.3)
def looks_for_one() -> None:
    check(scenario.player.looked_for == set(), 'nothing looked for')
    mineral = mineral_name(remembered['asteroid'])
    scenario.press(panel().rows[mineral])
    remembered['mineral'] = mineral


@scenario.step(.3)
def closes() -> None:
    mineral = remembered['mineral']
    check(scenario.player.looked_for == {mineral}, f'{mineral} looked for')
    check(panel().rows[mineral].looked_for, 'and shown so')
    scenario.escape()
    asteroid = remembered['asteroid']
    x, y = asteroid.pos
    # Out of the screen, within reach
    scenario.put_ship((x + 2500, y), asteroid.velocity)


@scenario.step(.3)
def points_at_it() -> None:
    check(not panel().open, 'escape closes the scanner')
    check(scenario.game.playing, 'the game goes on')
    scenario.screenshot('chevrons')


scenario.run()
