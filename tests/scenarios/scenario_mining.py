""" Locking on an asteroid and mining it with the laser """

import math
from typing import Any

from .harness import Scenario, loneliest

scenario = Scenario('mining')
check = scenario.check
remembered: dict[str, Any] = {}


@scenario.step(1.)
def locks_on() -> None:
    rock = loneliest(scenario.game.system.asteroids)
    remembered['rock'] = rock
    x, y = rock.pos
    scenario.put_ship((x + 140, y), rock.velocity, angle=math.pi)
    scenario.player.miner.lock_on(rock, scenario.player.ship.position)


@scenario.step(3.)
def mines() -> None:
    player = scenario.player
    check(player.ship is not None, 'the ship holds without crashing')
    if player.ship is None:
        return
    rock = remembered['rock']
    distance = math.dist(player.ship.position, rock.pos)
    check(abs(distance - 120) < 15, f'at mining distance: {distance:.0f}')
    check(player.miner.ore.get('rock', 0.) > 0, 'the laser mines it')
    rows = scenario.game.ids.cargo.ids
    check('empty' in rows and rows.empty.opacity == 0,
          'the cargo shows the rock')


scenario.run()
