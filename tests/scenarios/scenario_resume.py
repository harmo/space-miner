""" Leaving the game and coming back: left in flight, the ship comes back
on the Earth and its cargo is lost; left landed, at an outpost, it comes
back there with its cargo. Plays three sessions sharing their data, each
in a process of its own. """

import math
import os
import subprocess
import sys
import tempfile

SESSION = os.environ.get('SESSION')


def drive() -> int:
    data = tempfile.mkdtemp('-space-miner')
    for session in ('1', '2', '3'):
        result = subprocess.run(
            [sys.executable, '-m', 'tests.scenarios.scenario_resume'],
            env={**os.environ, 'SESSION': session, 'SPACE_MINER_DATA': data},
        )
        if result.returncode:
            return result.returncode
    return 0


if SESSION is None:
    sys.exit(drive())

# Imported once the session has its data folder
from typing import Any  # noqa: E402

from app.logic.ship.config import LANDING_DURATION  # noqa: E402

from .harness import Scenario  # noqa: E402

scenario = Scenario(f'resume, session {SESSION}')
check = scenario.check
remembered: dict[str, Any] = {}


def frontier() -> Any:
    return next(o for o in scenario.game.outposts if o.key == 'frontier')


if SESSION == '1':
    @scenario.step(1.)
    def takes_off() -> None:
        remembered['touch'] = scenario.hold_towards(
            scenario.away_from_earth()
        )

    @scenario.step(1.)
    def leaves_in_flight() -> None:
        remembered['touch'].touch_up()
        scenario.player.miner.ore['iron'] = 10.
        check(scenario.player.parking is None, 'flying')
        scenario.game.save()

elif SESSION == '2':
    @scenario.step(1.)
    def comes_back_on_the_earth() -> None:
        check(scenario.base.docked, 'on the Earth')
        check(scenario.player.miner.ore == {}, 'its cargo lost')
        outpost = frontier()
        x, y = outpost.pos
        direction = outpost.direction
        scenario.put_ship(
            (x + math.cos(direction) * 150, y + math.sin(direction) * 150),
            outpost.body.velocity, angle=direction,
        )

    @scenario.step(.3)
    def lands_at_the_frontier() -> None:
        scenario.player.land()

    @scenario.step(LANDING_DURATION + .5)
    def leaves_landed() -> None:
        check(scenario.game.ids.outpost.docked, 'landed on its pad')
        scenario.player.miner.ore['gold'] = 4.
        scenario.game.save()

else:
    @scenario.step(1.)
    def comes_back_where_it_landed() -> None:
        player = scenario.player
        check(player.docked_on(frontier().body), 'at the frontier')
        check(scenario.game.ids.outpost.docked, 'on its pad')
        check(player.miner.ore == {'gold': 4.}, f'with its cargo: '
              f'{player.miner.ore}')

scenario.run()
