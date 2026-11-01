""" Belts mined out growing back, and a swarm of rich asteroids passing
by """

import math
from typing import Any

from app.logic.world.config import (
    REGROW_AWAY,
    REGROW_THRESHOLD,
    SWARM_ASTEROIDS,
)
from app.logic.world.swarms import RICH

from .harness import Scenario

scenario = Scenario('events')
check = scenario.check
remembered: dict[str, Any] = {}


def events() -> Any:
    return scenario.game.system.events


@scenario.step(1.)
def mines_a_belt_out() -> None:
    # A whole belt in 30 seconds rather than minutes
    for regrowth in events().regrowths:
        regrowth.time = 30.
    system = scenario.game.system
    belt = system.belts[0]
    full = system.belt_plans[0].full
    for asteroid in belt[int(full * REGROW_THRESHOLD) - 2:]:
        system.remove(asteroid)
    remembered['left'] = len(belt)
    remembered['before'] = set(belt)


@scenario.step(5.)
def grows_back() -> None:
    system = scenario.game.system
    belt = system.belts[0]
    check(len(belt) > remembered['left'],
          f'the belt grows back: {remembered["left"]} then {len(belt)}')
    ship = scenario.player.anchor
    new = [rock for rock in belt if rock not in remembered['before']]
    check(all(asteroid in system.asteroids for asteroid in new),
          'with asteroids to mine')
    check(all(math.dist(asteroid.pos, ship) > REGROW_AWAY * .8
              for asteroid in new), 'out of the sight of the ship')
    events().swarm_clock.waiting = 0.


@scenario.step(.5)
def a_swarm_arrives() -> None:
    swarm = events().swarm
    check(len(swarm) == SWARM_ASTEROIDS, 'a swarm arrives')
    check(all(asteroid.mineral in RICH for asteroid in swarm), 'rich')
    check(events().headline.startswith('Essaim riche de passage'),
          f'and is told: {events().headline}')
    check(scenario.game.ids.news_label.text == events().headline,
          'at the top of the screen')
    # The loneliest, not to bump into another
    asteroid = max(swarm, key=lambda rock: min(
        math.dist(rock.pos, other.pos)
        for other in scenario.game.system.asteroids if other is not rock
    ))
    x, y = asteroid.pos
    scenario.put_ship((x + 140, y), asteroid.velocity, angle=math.pi)
    scenario.player.miner.lock_on(asteroid, scenario.player.ship.position)
    remembered['locked'] = asteroid


@scenario.step(1.5)
def mines_it() -> None:
    scenario.screenshot('swarm')
    check(scenario.player.ship is not None, 'the ship holds there')
    check(scenario.player.miner.lock is not None, 'locked on the swarm')
    events().swarm_clock.left = .01


@scenario.step(.5)
def the_swarm_leaves() -> None:
    system = scenario.game.system
    check(events().swarm == [], 'the swarm leaves')
    check(remembered['locked'] not in system.asteroids, 'with its asteroids')
    check(scenario.player.miner.lock is None,
          'the ship stops mining what left')
    check(events().headline == "L'essaim a quitté le système",
          f'which is told: {events().headline}')


scenario.run()
