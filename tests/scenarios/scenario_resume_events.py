""" Leaving the game with things going on: canisters around a planet, a
comet with what it shed, a swarm, a flare and its ejecta all come back as
they were, those mined staying gone. Plays two sessions sharing their
data, each in a process of its own. """

import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SESSION = os.environ.get('SESSION')


def drive() -> int:
    data = tempfile.mkdtemp('-space-miner')
    for session in ('1', '2'):
        result = subprocess.run(
            [sys.executable, '-m', 'tests.scenarios.scenario_resume_events'],
            env={**os.environ, 'SESSION': session, 'SPACE_MINER_DATA': data},
        )
        if result.returncode:
            return result.returncode
    return 0


if SESSION is None:
    sys.exit(drive())

# Imported once the session has its data folder
from app.logic.mining.canisters import eject_cargo  # noqa: E402

from .harness import Scenario  # noqa: E402

scenario = Scenario('resume_events')
check = scenario.check
DATA = Path(os.environ['SPACE_MINER_DATA'])


def system() -> Any:
    return scenario.game.system


def events() -> Any:
    return system().events


def planet() -> Any:
    return system().planets[-1]


def lose_cargo() -> None:
    body = planet()
    scenario.player.canisters.add(eject_cargo(
        scenario.game.rng, {'gold': 25.},
        (body.pos[0] + body.radius + 200, body.pos[1]), body.velocity, 0.,
    ))


def make_things_happen() -> None:
    lose_cargo()
    events().comet_clock.waiting = 0.
    events().clock.waiting = 0.
    flares = events().flares.clock
    flares.phase, flares.left = 'blazing', 0.


def mine_some() -> None:
    check(events().comet is not None, 'a comet')
    check(bool(events().swarm), 'a swarm')
    check(bool(events().flares.ejecta), 'ejecta')
    system().remove(events().debris[0])
    system().remove(events().swarm[0])
    system().remove(events().flares.ejecta[0])


def remember() -> None:
    orbit, body = events().comet_orbit, planet()
    canisters = scenario.player.canisters.canisters
    (DATA / 'then.json').write_text(json.dumps({
        'canisters': len(canisters),
        'offsets': [
            math.dist(canister.pos, body.pos) for canister in canisters
        ],
        'amount': sum(canister.amount for canister in canisters),
        'anomaly': orbit.anomaly, 'tilt': orbit.tilt,
        'debris': sorted(a.mineral for a in events().debris),
        'shed': events().shed,
        'swarm': len(events().swarm),
        'swarm_left': events().clock.left,
        'ejecta': len(events().flares.ejecta),
        'flare_left': events().flares.clock.left,
    }))
    scenario.game.save()


def comes_back() -> None:
    then = json.loads((DATA / 'then.json').read_text())
    canisters = scenario.player.canisters.canisters
    check(len(canisters) == then['canisters'],
          f'the canisters are back: {len(canisters)}')
    amount = sum(canister.amount for canister in canisters)
    check(abs(amount - then['amount']) < 1e-6, f'with their ore: {amount}')
    body = planet()
    check(all(
        abs(math.dist(canister.pos, body.pos) - offset) < 300
        for canister, offset in zip(canisters, then['offsets'], strict=True)
    ), 'around the same planet')
    orbit = events().comet_orbit
    check(orbit is not None, 'the comet is back')
    check(abs(orbit.anomaly - then['anomaly']) < .02, 'as far along')
    check(orbit.tilt == then['tilt'], 'on the same way')
    debris = sorted(a.mineral for a in events().debris)
    check(len(debris) >= len(then['debris']), f'with its debris: {debris}')
    check(events().shed >= then['shed'], 'what was mined stays gone')
    check(len(events().swarm) == then['swarm'], 'the swarm is back')
    check(abs(events().clock.left - then['swarm_left']) < 3, 'for as long')
    check(len(events().flares.ejecta) == then['ejecta'], 'the ejecta too')
    check(events().flares.clock.phase == 'ejecta', 'the flare goes on')
    check(abs(events().flares.clock.left - then['flare_left']) < 3,
          'for as long')


if SESSION == '1':
    scenario.step(1.)(make_things_happen)
    scenario.step(.5)(mine_some)
    scenario.step(.2)(remember)
else:
    scenario.step(.2)(comes_back)

scenario.run()
