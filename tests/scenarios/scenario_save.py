""" The game saved, and back as it was in the next session, with its
solar system. Then the settings, a new game, and an unreadable save.
Plays three sessions sharing their data, each in a process of its own.
"""

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

SESSION = os.environ.get('SESSION')


def drive() -> int:
    """ The sessions one after the other, with different seeds: the saved
    one must win """
    data = tempfile.mkdtemp('-space-miner')
    for session in ('1', '2', '3'):
        if session == '3':
            Path(data, 'save.json').write_text('garbage')
        result = subprocess.run(
            [sys.executable, '-m', 'tests.scenarios.scenario_save'],
            env={**os.environ, 'SESSION': session, 'SPACE_MINER_DATA': data,
                 'SPACE_MINER_SEED': session},
        )
        if result.returncode:
            return result.returncode
    return 0


if SESSION is None:
    sys.exit(drive())

# Imported once the session has its data folder
from app.logic.base.missions import Mission  # noqa: E402
from app.logic.ship.shipyard import Design  # noqa: E402

from .harness import Scenario  # noqa: E402

scenario = Scenario(f'save, session {SESSION}')
check = scenario.check
DATA = Path(scenario.data)
DESIGN = Design(parts={'nose': 'laser', 'left': 'fins'})
MISSION = Mission('Fonderie Lunaire', {'iron': 12}, 500)
Steps = list[tuple[float, Callable[[], None]]]


def planets() -> list[float]:
    return [round(planet.radius) for planet in scenario.game.system.planets]


# Session 1: playing

def plays() -> None:
    base, player = scenario.base, scenario.player
    base.wallet.earn(9000)
    base.board.validated = 4
    base.inventory.add('engine')
    player.refit(DESIGN)
    base.depot.stock.update({'iron': 12.5})
    player.miner.ore.update({'gold': 4.})
    base.board.offers[0] = MISSION
    base.board.accept(MISSION)
    (DATA / 'planets.json').write_text(json.dumps(planets()))


def saved() -> None:
    saved = json.loads((DATA / 'save.json').read_text())
    check(saved['credits'] == 9000, 'saved on its own')


# Session 2: back, then a new game

def comes_back() -> None:
    base, player = scenario.base, scenario.player
    check(base.wallet.credits == 9000, 'the credits are back')
    check(player.design == DESIGN, 'the ship is back')
    check(base.inventory.spares == {'engine': 1}, 'the hangar is back')
    check(base.depot.stock == {'iron': 12.5}, 'the depot is back')
    check(player.miner.ore == {'gold': 4.}, 'the cargo is back')
    check(base.board.active == [MISSION] and base.board.validated == 4,
          'the missions are back')
    check(planets() == json.loads((DATA / 'planets.json').read_text()),
          'the solar system is back')
    check(player.parking is not None, 'landed on the Earth')
    scenario.game.playing = False
    scenario.press(scenario.button(scenario.game.ids.home, 'Réglages'))


def changes_a_setting() -> None:
    panel = scenario.game.ids.settings
    check(scenario.game.settings_open, 'the settings open')
    row = next(w for w in panel.walk() if getattr(w, 'name', '') == 'orbits')
    scenario.press(scenario.button(row, 'Oui'))
    ambience = next(
        w for w in panel.walk() if getattr(w, 'name', '') == 'ambience'
    )
    next(w for w in ambience.walk() if hasattr(w, 'step')).value = .3
    scenario.screenshot('settings')
    preferences = json.loads((DATA / 'preferences.json').read_text())
    check(preferences['orbits'] is False, 'the setting is saved')
    check(preferences['ambience'] == .3, 'so is the volume')
    check(scenario.game.preferences.ambience == .3, 'heard at once')
    scenario.press(scenario.button(panel, 'Nouvelle partie'))


def confirms() -> None:
    panel = scenario.game.ids.settings
    check(panel.confirming, 'a new game takes a confirmation')
    scenario.press(scenario.button(panel, 'Tout effacer'))


def starts_over() -> None:
    base, player = scenario.base, scenario.player
    check(base.wallet.credits == 0 and player.design == Design(),
          'a new game starts over')
    check(base.board.validated == 0 and base.depot.stock == {},
          'with no reputation nor ore')
    check(json.loads((DATA / 'save.json').read_text())['credits'] == 0,
          'and is saved')
    check(scenario.game.preferences.orbits is False,
          'the settings stay')


# Session 3: an unreadable save

def starts_anew() -> None:
    check(scenario.base.wallet.credits == 0, 'a fresh game')
    check((DATA / 'save.unreadable.json').read_text() == 'garbage',
          'the unreadable save is kept aside')


SESSIONS: dict[str, Steps] = {
    '1': [(1., plays), (6., saved)],
    '2': [(1., comes_back), (.4, changes_a_setting), (.3, confirms),
          (.4, starts_over)],
    '3': [(1., starts_anew)],
}
for delay, step in SESSIONS[SESSION]:
    scenario.step(delay)(step)

scenario.run()
