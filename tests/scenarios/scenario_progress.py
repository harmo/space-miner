""" Parts of higher tiers, sold as missions are validated """

from typing import Any

from app.logic.base.config import TIER_MISSIONS

from .harness import Scenario

scenario = Scenario('progress')
check = scenario.check


def hangar() -> Any:
    return scenario.base.ids.hangar


def level_buttons() -> list[Any]:
    """ From the first level """
    levels = scenario.base.ids.missions.ids.levels.children
    return sorted(
        (button for button in levels if hasattr(button, 'level')),
        key=lambda button: button.level,
    )


def names() -> list[str]:
    return [row.name for row in reversed(hangar().ids.parts.children)]


@scenario.step(1.)
def opens() -> None:
    scenario.press(scenario.base.ids.hangar_button)


@scenario.step(.4)
def first_tier() -> None:
    check(names() == ['Rien', 'Laser renforcé', 'Carénage',
                      'Soute frontale'], f'the first tier only: {names()}')
    check(f'0 / {TIER_MISSIONS[1]}' in hangar().teaser,
          'the next tier is announced')
    scenario.escape()
    scenario.base.board.validated = TIER_MISSIONS[1]


@scenario.step(.3)
def announces_new_parts() -> None:
    check(scenario.base.new_parts, 'the hangar glows for new parts')
    scenario.press(scenario.base.ids.hangar_button)


@scenario.step(.4)
def second_tier() -> None:
    check('Laser lourd' in names(), 'the second tier is sold')
    check('Laser quantique' not in names(), 'not the fourth one yet')
    check(not scenario.base.new_parts, 'seen once the hangar opens')
    scenario.escape()
    scenario.base.board.validated = TIER_MISSIONS[1] + 1


@scenario.step(.3)
def shows_the_reputation() -> None:
    scenario.press(scenario.base.ids.missions_button)


@scenario.step(.4)
def reputation() -> None:
    text = scenario.base.ids.missions.reputation
    check(text.startswith('Réputation : palier 2'), text)
    check(f'palier 3 à {TIER_MISSIONS[2]}' in text, text)


@scenario.step(.1)
def at_the_top() -> None:
    levels = level_buttons()
    check([button.reached for button in levels] == [True, True] + [False] * 3,
          'missions up to the second level, at the second tier')
    board = scenario.base.board
    board.validated = TIER_MISSIONS[-1]
    board.choose_level(5)
    scenario.base.ids.missions.refresh()


@scenario.step(.4)
def eight_missions() -> None:
    missions = scenario.base.ids.missions
    scenario.screenshot('missions')
    board = scenario.base.board
    check(len(board.offers) == 8 and board.most == 8,
          'eight offers, eight missions at a time')
    offers = missions.ids.offers
    check(len(offers.children) == 8, 'all of them shown')
    check(offers.parent.parent.height < offers.height, 'which scroll')
    check(missions.accepted == '0/8', missions.accepted)
    check(all(mission.level == 5 for mission in board.offers),
          'offers of the top level')
    scenario.press(level_buttons()[0])


@scenario.step(.3)
def chooses_small_ones() -> None:
    board = scenario.base.board
    check(board.level == 1, 'the first level chosen')
    check(all(mission.level == 1 for mission in board.offers),
          'offers of the first level')
    check(level_buttons()[0].chosen, 'and shown so')


scenario.run()
