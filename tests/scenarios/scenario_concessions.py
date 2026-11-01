""" Concessions: the mine of Ares stays locked on its site until the
concession is validated on the Earth, once the reputation allows it """

import math
from typing import Any

from app.logic.base.config import TIER_MISSIONS
from app.logic.base.missions import needs_at
from app.logic.base.sites import ARES_MINE
from app.logic.ship.config import LANDING_DURATION

from .harness import Scenario

scenario = Scenario('concessions')
check = scenario.check


def ares() -> Any:
    return next(o for o in scenario.game.outposts if o.key == 'ares')


def missions() -> Any:
    return scenario.base.ids.missions


def permit_cards() -> list[Any]:
    return list(missions().ids.permits.children)


@scenario.step(1.)
def opens_the_missions() -> None:
    scenario.press(scenario.base.ids.missions_button)


@scenario.step(.3)
def has_none_at_first() -> None:
    check(not permit_cards(), 'no concession without a reputation')
    scenario.escape()
    outpost = ares()
    for stage in outpost.construction.site.stages[:2]:
        outpost.deliver({name: float(n) for name, n in stage.materials})
    x, y = outpost.pos
    direction = outpost.direction
    scenario.put_ship(
        (x + math.cos(direction) * 120, y + math.sin(direction) * 120),
        outpost.body.velocity, angle=direction,
    )


@scenario.step(.3)
def lands_at_ares() -> None:
    scenario.player.land()


@scenario.step(LANDING_DURATION + .5)
def finds_its_mine_locked() -> None:
    view = scenario.game.ids.outpost
    check(view.docked, 'at Ares')
    stage = ares().construction.stage
    check(stage.name == 'Mine', f'its mine comes next: {stage.name}')
    check(ares().construction.locked, 'locked')
    scenario.player.miner.ore.update(
        {name: float(n) for name, n in stage.materials}
    )
    scenario.press(view.ids.site_button)


@scenario.step(.3)
def is_told_why() -> None:
    panel = scenario.game.ids.outpost.ids.site
    check('Mine de Mars' in panel.adds, f'told: {panel.adds}')
    check(not panel.can_deliver, 'nothing can be delivered')
    scenario.screenshot('locked')
    scenario.press(scenario.button(panel, 'Fermer'))
    scenario.player.restart(scenario.player.design)
    scenario.player.miner.ore.clear()
    base = scenario.base
    base.board.validated = TIER_MISSIONS[1]
    base.depot.stock.update({
        name: float(units) for name, units in ARES_MINE.mission.wanted.items()
    })


@scenario.step(.5)
def opens_the_missions_again() -> None:
    scenario.press(scenario.base.ids.missions_button)


@scenario.step(.3)
def offers_the_concession() -> None:
    cards = permit_cards()
    check(len(cards) == 2, f'two at this reputation: {len(cards)}')
    scenario.screenshot('offered')
    card = next(c for c in cards if c.permit is ARES_MINE)
    check(card.can_act, 'it can be validated')
    scenario.press(scenario.button(card, 'Suivre'))


@scenario.step(.3)
def follows_it() -> None:
    base, game = scenario.base, scenario.game
    check(base.permits.followed == {ARES_MINE.key}, 'followed')
    wanted = {need.mineral for need in needs_at(game.desks, {})}
    check(wanted == set(ARES_MINE.mission.wanted), f'tracked: {wanted}')
    check(game.ids.tracker.shown, 'shown in flight')
    check(not base.board.active, 'taking no place among the missions')
    check(game.keeper.snapshot().followed == [ARES_MINE.key], 'and saved')
    card = next(c for c in permit_cards() if c.permit is ARES_MINE)
    scenario.button(card, 'Ne plus suivre')
    scenario.screenshot('followed')
    scenario.press(scenario.button(card, 'Valider'))


@scenario.step(.3)
def grants_it() -> None:
    base = scenario.base
    check(not base.permits.lacks(ARES_MINE), 'the concession is granted')
    check(not base.permits.followed, 'not followed anymore')
    # Some of it filling the tank right away
    reward = ARES_MINE.mission.reward
    check(reward - 50 < base.wallet.credits <= reward,
          f'paid: {base.wallet.credits}')
    check(not base.depot.stock, 'the ore goes')
    check(len(permit_cards()) == 1, 'the other one is left')
    check(not ares().construction.locked, 'the mine can be built')
    scenario.escape()


scenario.run()
