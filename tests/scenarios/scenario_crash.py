""" Crashing into an asteroid: the cargo flies away in canisters, and the
ship comes back on the Earth """

import pytest

from app.logic.ship.config import RESPAWN_DELAY

from .harness import Scenario

scenario = Scenario('crash')
check = scenario.check
CARGO = {'iron': 20., 'gold': 5.}


@scenario.step(1.)
def rushes_into_an_asteroid() -> None:
    scenario.player.miner.ore.update(CARGO)
    asteroid = scenario.game.system.asteroids[0]
    x, y = asteroid.pos
    vx, vy = asteroid.velocity
    scenario.put_ship(
        (x + asteroid.radius + 25, y), (vx - 400, vy), angle=3.14,
    )


@scenario.step(.5)
def explodes() -> None:
    player = scenario.player
    check(player.ship is None, 'touching an asteroid is fatal')
    check(bool(player.explosions), 'the ship explodes')
    check(player.miner.ore == {}, 'the cargo is lost')
    lost: dict[str, float] = {}
    for canister in player.canisters.canisters:
        lost[canister.mineral] = lost.get(canister.mineral, 0.) + (
            canister.amount
        )
    check(lost == pytest.approx(CARGO), f'into canisters: {lost}')


@scenario.step(RESPAWN_DELAY + .5)
def comes_back() -> None:
    player = scenario.player
    check(player.ship is not None, 'a new ship comes')
    check(scenario.base.docked, 'landed on the Earth')
    check(len(player.canisters.canisters) > 0,
          'the canisters wait to be picked up')


scenario.run()
