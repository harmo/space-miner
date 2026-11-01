""" Missions: two at a time, validated by hand from the depot, followed
while flying """

from typing import Any

from kivy.core.text import Label as CoreLabel

from app.logic.base.missions import Mission

from .harness import Scenario

scenario = Scenario('missions')
check = scenario.check
FIRST = Mission('Fonderie Lunaire', {'iron': 12, 'crystal': 5}, 500)
SECOND = Mission('Laboratoire Kepler', {'iron': 6, 'ruby': 3}, 600)


def panel() -> Any:
    return scenario.base.ids.missions


LONGEST = Mission('Chantier orbital Vesta', {'iron': 5}, 123456, 5)


def cards(kind: str) -> list[Any]:
    return list(reversed(panel().ids[kind].children))


@scenario.step(1.)
def opens() -> None:
    board = scenario.base.board
    board.offers[0], board.offers[1] = FIRST, SECOND
    board.offers[2] = LONGEST
    scenario.press(scenario.base.ids.missions_button)


@scenario.step(.4)
def shows_names_in_full() -> None:
    card = cards('offers')[2]
    label = next(
        widget for widget in card.walk()
        if getattr(widget, 'text', None) == LONGEST.client
    )
    text = CoreLabel(
        text=LONGEST.client, font_size=label.font_size, bold=True,
    )
    text.refresh()
    check(text.texture.width <= label.width,
          f'the longest name fits: {text.texture.width} in {label.width}')
    scenario.screenshot('names')


@scenario.step(.4)
def accepts_the_first() -> None:
    check(scenario.base.panel == 'missions', 'the missions open')
    check(all(card.can_act for card in cards('offers')),
          'offers can be accepted')
    scenario.press(scenario.button(cards('offers')[0], 'Accepter'))


@scenario.step(.3)
def accepts_the_second() -> None:
    check(scenario.base.board.active == [FIRST], 'the first is accepted')
    scenario.press(scenario.button(cards('offers')[0], 'Accepter'))


@scenario.step(.3)
def no_more_than_two() -> None:
    board = scenario.base.board
    check(board.active == [FIRST, SECOND], 'two missions under way')
    check(not any(card.can_act for card in cards('offers')),
          'a third one can not be accepted')
    check(len(board.offers) == 1, 'accepted offers are not replaced yet')
    coming = scenario.base.ids.missions.coming
    check('Prochaine mission' in coming, f'one comes later: {coming}')
    check(not any(card.can_act for card in cards('active')),
          'nothing to validate without the ore')
    scenario.screenshot('recharging')
    board.waits[1] = .1


@scenario.step(.8)
def an_offer_comes_back() -> None:
    check(len(scenario.base.board.offers) == 2, 'an offer comes back')
    check(len(cards('offers')) == 2, 'and shows at once')
    scenario.escape()


@scenario.step(.3)
def flies_with_the_needs() -> None:
    base, player = scenario.base, scenario.player
    base.depot.stock.update({'iron': 10., 'crystal': 5.})
    player.miner.ore.update({'iron': 4.})
    if scenario.game.compact:
        scenario.game.toggle_cargo()        # the needs show under it
    remembered['touch'] = scenario.hold_towards(scenario.away_from_earth())


@scenario.step(1.)
def shows_the_needs() -> None:
    remembered['touch'].touch_up()
    tracker = scenario.game.ids.tracker
    rows = [
        (row.name, row.progress, row.met, row.laser)
        for row in reversed(tracker.ids.rows.children)
    ]
    check(tracker.opacity == 1, 'the needs show while flying')
    check(rows == [
        ('Fer', '14 / 18', False, ''), ('Cristal', '5 / 5', True, ''),
        ('Rubis', '0 / 3', False, '3'),
    ], f'the needs add up, in the cargo and the depot: {rows}')
    ground = scenario.player.grounds.spots(scenario.player.grounds.home)
    scenario.put_ship(scenario.above_earth(ground[len(ground) // 2], 200.),
                      scenario.game.system.earth.velocity)


@scenario.step(.3)
def lands() -> None:
    scenario.player.land()


@scenario.step(3.5)
def not_enough_yet() -> None:
    base = scenario.base
    check(base.docked, 'back on the Earth')
    # 6 iron in the depot, 4 still in the cargo: 2 lacking
    base.depot.stock['iron'] = 6.
    scenario.press(base.ids.missions_button)


@scenario.step(.4)
def lacking() -> None:
    check(not cards('active')[0].can_act, 'two iron are lacking')
    # Unloaded meanwhile, the panel open
    scenario.base.depot.stock['iron'] = 10.


@scenario.step(.8)
def validated() -> None:
    first = cards('active')[0]
    check(first.can_act, 'enough with the depot and the cargo, at once')
    # Full, the base buys no fuel with the reward
    tank = scenario.player.tank
    tank.fill(tank.capacity)
    scenario.press(scenario.button(first, 'Valider'))


@scenario.step(.3)
def paid() -> None:
    base = scenario.base
    check(base.wallet.credits == FIRST.reward, 'the mission is paid')
    check(base.depot.stock == {}, 'its ore is taken from the depot')
    check(scenario.player.miner.ore == {'iron': 2.},
          'then from the cargo')
    check(base.board.validated == 1, 'the reputation grows')
    scenario.press(scenario.button(cards('active')[0], 'Abandonner'))


@scenario.step(.3)
def abandoned() -> None:
    check(scenario.base.board.active == [], 'the second is abandoned')
    scenario.escape()


@scenario.step(.3)
def closed() -> None:
    check(scenario.base.panel == '', 'escape closes the missions')


remembered: dict[str, Any] = {}

scenario.run()
