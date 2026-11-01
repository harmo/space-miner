""" Canisters lost close to the sun gather on an orbit around it, inside
that of the first planet, where a ship picks one up, in a hurry """

import math
from typing import Any

from app.logic.mining.canisters import eject_cargo
from app.logic.mining.config import (
    CANISTER_ORBIT_ALTITUDE,
    CANISTER_SUN_ALTITUDE,
)

from .harness import Scenario

scenario = Scenario('canister_sun')
check = scenario.check
remembered: dict[str, Any] = {}


def sun() -> Any:
    return scenario.game.system.sun


def canisters() -> Any:
    return scenario.player.canisters.canisters


def altitude(canister: Any) -> float:
    return float(math.dist(canister.pos, sun().pos) - sun().radius)


@scenario.step(1.)
def loses_cargo_close_to_the_sun() -> None:
    planets = scenario.game.system.planets
    # On the side away from the two closest planets
    x, y = planets[0].pos
    away = math.atan2(y - sun().pos[1], x - sun().pos[0]) + math.pi
    distance = sun().radius + 1200
    scenario.player.canisters.add(eject_cargo(
        scenario.game.rng, {'gold': 30.},
        (sun().pos[0] + math.cos(away) * distance,
         sun().pos[1] + math.sin(away) * distance),
        (0., 0.), away,
    ))
    check(len(canisters()) >= 3, f'in canisters: {len(canisters())}')


@scenario.step(14.)
def they_gather_around_it() -> None:
    low, high = CANISTER_ORBIT_ALTITUDE
    for canister in canisters():
        height = altitude(canister)
        check(CANISTER_SUN_ALTITUDE + low - 40 < height
              < CANISTER_SUN_ALTITUDE + high + 40,
              f'on their orbit: {height:.0f}')
        x = canister.pos[0] - sun().pos[0]
        y = canister.pos[1] - sun().pos[1]
        vx, vy = canister.velocity
        check(x * vy - y * vx > 0, 'turning around it')
        check(math.hypot(vx, vy) > 20, f'moving: {math.hypot(vx, vy):.0f}')
    canister = max(canisters(), key=altitude)
    away = math.atan2(
        canister.pos[1] - sun().pos[1], canister.pos[0] - sun().pos[0],
    )
    scenario.put_ship(
        (canister.pos[0] + math.cos(away) * 60,
         canister.pos[1] + math.sin(away) * 60),
        canister.velocity,
    )
    scenario.player.heat.level = 0.
    remembered['count'] = len(canisters())
    player = scenario.player
    player.miner.work_at(canister.pos, 40., player.ship.position)


@scenario.step(.4)
def picks_one_up_in_a_hurry() -> None:
    check(len(canisters()) < remembered['count'], 'one is picked up')
    check(scenario.player.ship is not None, 'safe and sound')
    check(scenario.player.heat.level > 0, 'the hull heats up there')


scenario.run()
