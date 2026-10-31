""" Buying hulls, and moving the ship onto them with its parts """

import math
from typing import Any

import pytest

from app.logic.base.config import TIER_MISSIONS
from app.logic.ship.config import LEG_LENGTH
from app.logic.ship.hulls import HULLS
from app.logic.ship.shipyard import Design

from .harness import Scenario

scenario = Scenario('hulls')
check = scenario.check
START = Design(parts={'nose': 'laser', 'left': 'fins', 'right': 'fins'})


def hangar() -> Any:
    return scenario.base.ids.hangar


def rows() -> dict[str | None, Any]:
    return {row.part: row for row in hangar().ids.parts.children}


def slot_button(slot_id: str) -> Any:
    return next(
        button for button in hangar().ids.slots.children
        if button.slot == slot_id
    ).children[0]


def standing() -> float:
    """ How far the rear of the ship is from the ground """
    player = scenario.player
    earth = scenario.game.system.earth
    distance = math.dist(player.ship.position, earth.pos)
    return float(distance - earth.radius - player.stats.size.length / 2)


@scenario.step(1.)
def opens_the_hulls() -> None:
    base = scenario.base
    base.wallet.earn(100000)
    base.board.validated = TIER_MISSIONS[-1]
    for hull in ('hauler', 'cruiser'):
        base.depot.stock.update(
            {name: float(units) for name, units in HULLS[hull].materials}
        )
    scenario.player.refit(START)
    scenario.press(base.ids.hangar_button)


@scenario.step(.4)
def lists_them() -> None:
    scenario.press(slot_button('hull'))


@scenario.step(.4)
def buys_the_hauler() -> None:
    scenario.screenshot('hulls')
    check(set(rows()) == set(HULLS), f'every hull is sold: {set(rows())}')
    check(rows()['scout'].action == 'fitted', 'on the scout')
    remembered['length'] = scenario.player.stats.size.length
    scenario.press(scenario.button(rows()['hauler'], 'Acheter'))


@scenario.step(.4)
def moved_onto_it() -> None:
    player = scenario.player
    check(player.design.hull == 'hauler', 'the ship moves onto it')
    check(sorted(player.design.parts.values()) == ['fins', 'fins', 'laser'],
          'with its parts')
    check(player.stats.capacity >= HULLS['hauler'].capacity, 'roomier')
    check(player.stats.size.length > remembered['length'], 'bigger')
    check(standing() == pytest.approx(LEG_LENGTH, abs=.5),
          f'standing on its legs: {standing():.1f}')
    scenario.press(scenario.button(rows()['cruiser'], 'Acheter'))


@scenario.step(.4)
def eight_slots() -> None:
    scenario.screenshot('cruiser')
    check(scenario.player.design.hull == 'cruiser', 'onto the cruiser')
    slots = hangar().ids.slots
    check(len(slots.children) == 1 + len(HULLS['cruiser'].slots),
          'the hull and its slots')
    check(slots.parent.height < slots.height, 'which scroll')
    scenario.press(scenario.button(rows()['scout'], 'Choisir'))


@scenario.step(.4)
def back_on_the_scout() -> None:
    base, player = scenario.base, scenario.player
    check(player.design == START, 'back on the scout, as it was')
    check(base.inventory.hulls == set(HULLS) - {'driller'},
          'the hulls stay in the hangar')
    scenario.escape()


@scenario.step(.3)
def flies() -> None:
    remembered['touch'] = scenario.hold_towards(scenario.away_from_earth())


@scenario.step(1.)
def flew() -> None:
    remembered['touch'].touch_up()
    check(scenario.player.ship is not None and not scenario.base.docked,
          'the ship takes off')


remembered: dict[str, Any] = {}

scenario.run()
