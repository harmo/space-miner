""" Crashing into a planet: the canisters gather on an orbit close to it,
those lost far away from it too, where the next ship picks them up """

import math
from typing import Any

from app.logic.mining.canisters import eject_cargo
from app.logic.mining.config import (
    CANISTER_ORBIT_ALTITUDE,
    CANISTER_ORBIT_PACE,
)

from .harness import Scenario

scenario = Scenario('canister_orbit')
check = scenario.check
remembered: dict[str, Any] = {}


def planet() -> Any:
    """ With no asteroids of its own, which canisters would turn with """
    system = scenario.game.system
    ringed = {asteroid.orbit.parent for asteroid in system.asteroids}
    return next(
        body for body in reversed(system.planets)
        if body not in ringed and body is not system.earth
    )


def canisters() -> Any:
    return scenario.player.canisters.canisters


def loneliness(canister: Any) -> float:
    """ How far from the others it is, in the way of no ship """
    return min(
        math.dist(canister.pos, other.pos)
        for other in canisters() if other is not canister
    )


def relative(canister: Any) -> tuple[float, float, float, float]:
    """ Its position, then its velocity, from the planet """
    body = planet()
    return (
        canister.pos[0] - body.pos[0], canister.pos[1] - body.pos[1],
        canister.velocity[0] - body.velocity[0],
        canister.velocity[1] - body.velocity[1],
    )


@scenario.step(1.)
def rushes_into_a_planet() -> None:
    scenario.player.miner.ore.update({'iron': 40., 'gold': 10.})
    body = planet()
    x, y = body.pos
    vx, vy = body.velocity
    scenario.put_ship(
        (x, y + body.radius + 40), (vx, vy - 500), angle=-math.pi / 2,
    )


@scenario.step(.5)
def explodes() -> None:
    check(scenario.player.ship is None, 'the ship explodes')
    check(len(canisters()) >= 5, f'into canisters: {len(canisters())}')
    scenario.screenshot('thrown')
    body = planet()
    x, y = body.pos
    far = (x + body.radius * 4.5, y)
    scenario.player.canisters.add(eject_cargo(
        scenario.game.rng, {'copper': 20.}, far, body.velocity, 0.,
    ))


@scenario.step(20.)
def settles_on_an_orbit() -> None:
    body = planet()
    for canister in canisters():
        x, y, vx, vy = relative(canister)
        distance = math.hypot(x, y)
        low, high = CANISTER_ORBIT_ALTITUDE
        check(low - 30 < distance - body.radius < high + 30,
              f'close to it: {distance - body.radius:.0f}')
        speed = math.hypot(vx, vy)
        circular = CANISTER_ORBIT_PACE * math.sqrt(
            math.hypot(*body.pull(*canister.pos)) * distance
        )
        check(abs(speed - circular) < .1 * circular,
              f'at orbital speed: {speed:.0f} for {circular:.0f}')
        check(abs(x * vx + y * vy) / distance < 15,
              f'around it: {x * vx + y * vy:.0f}')
    remembered['angles'] = [
        math.atan2(y, x) for x, y, _, _ in map(relative, canisters())
    ]


@scenario.step(1.)
def turns_around_it() -> None:
    angles = [math.atan2(y, x) for x, y, _, _ in map(relative, canisters())]
    check(angles != remembered['angles'], 'still moving around it')
    canister = max(canisters(), key=loneliness)
    remembered['canister'] = canister
    x, y, _, _ = relative(canister)
    distance = math.hypot(x, y)
    scenario.put_ship(
        (canister.pos[0] + x / distance * 60,
         canister.pos[1] + y / distance * 60),
        canister.velocity,
    )


@scenario.step(.2)
def flies_among_them() -> None:
    scenario.screenshot('orbit')
    canister = remembered['canister']
    remembered['count'] = len(canisters())
    player = scenario.player
    player.miner.work_at(canister.pos, 40., player.ship.position)


@scenario.step(.4)
def picks_one_up() -> None:
    check(len(canisters()) < remembered['count'], 'one is picked up')
    check(scenario.player.miner.ore, f'cargo: {scenario.player.miner.ore}')
    check(scenario.player.ship is not None, 'flying around safely')
    spins = [x * vy - y * vx for x, y, vx, vy in map(relative, canisters())]
    check(all(spin > 0 for spin in spins), 'all turning the same way')


scenario.run()
