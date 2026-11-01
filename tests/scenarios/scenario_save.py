""" The game saved, and back as it was in the next session, with its
solar system. Then the settings, a slot erased, and an unreadable save.
Plays three sessions sharing their data, each in a process of its own.
"""

import json
import math
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

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
from app.engine.entities import get_body  # noqa: E402
from app.logic.base.missions import Mission  # noqa: E402
from app.logic.ship.shipyard import Design  # noqa: E402

from .harness import Scenario  # noqa: E402

scenario = Scenario(f'save, session {SESSION}')
check = scenario.check
DATA = Path(scenario.data)
DESIGN = Design(parts={'nose': 'laser', 'left': 'fins'})
MISSION = Mission('Fonderie Lunaire', {'iron': 12}, 500)
Steps = list[tuple[float, Callable[[], None]]]


def first_slot() -> Any:
    slots = scenario.game.ids.home.ids.slots.children
    return next(card for card in slots if card.slot == 1)


def angles() -> list[float]:
    system = scenario.game.system
    return [body.orbit.angle for body in (system.earth, system.neptune)]


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
    # Far from where they start, the ship landed on one of them
    system = scenario.game.system
    moved = system.angles
    for body in (system.earth, system.neptune):
        moved[system.lasting.index(body)] += 1.
    system.resume_orbits(moved)


def saved() -> None:
    saved = json.loads((DATA / 'save.json').read_text())
    check(saved['credits'] == 9000, 'saved on its own')
    check(scenario.player.parking is not None, 'still landed')
    (DATA / 'angles.json').write_text(json.dumps(angles()))


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
    system = scenario.game.system
    before = json.loads((DATA / 'angles.json').read_text())
    check(all(abs(math.remainder(now - then, math.tau)) < .1
              for now, then in zip(angles(), before, strict=True)),
          f'the planets are back in their places: {angles()}, {before}')
    distance = math.dist(player.anchor, system.earth.pos)
    check(distance < system.earth.radius + 80,
          f'the ship on the Earth, wherever it is: {distance:.0f}')
    moon = next(b for b in system.lasting if b.orbit.parent is system.earth)
    body = get_body(scenario.game.gameworld, moon.entity_id)
    check(math.dist((body.position.x, body.position.y), moon.pos) < 5,
          'and all that turns around it')
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
    scenario.press(scenario.button(panel, 'Fermer'))
    scenario.press(scenario.button(first_slot(), 'Effacer'))


def confirms() -> None:
    check(first_slot().confirming, 'erasing takes a confirmation')
    scenario.press(scenario.button(first_slot(), 'Confirmer'))


def starts_over() -> None:
    base, player = scenario.base, scenario.player
    check(base.wallet.credits == 0 and player.design == Design(),
          'the game starts over')
    check(base.board.validated == 0 and base.depot.stock == {},
          'with no reputation nor ore')
    check(not (DATA / 'save.json').exists(), 'nothing left of it')
    scenario.press(scenario.button(first_slot(), first_slot().text))


def is_saved_again() -> None:
    check(scenario.game.playing, 'a new game in that slot')
    scenario.game.save()
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
          (.4, starts_over), (.4, is_saved_again)],
    '3': [(1., starts_anew)],
}
for delay, step in SESSIONS[SESSION]:
    scenario.step(delay)(step)

scenario.run()
