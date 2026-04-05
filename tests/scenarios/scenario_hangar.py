""" Buying parts, fitting them, selling them back, and selling ore """

from typing import Any

from app.logic.base.config import TIER_MISSIONS
from app.logic.base.market import ore_price
from app.logic.base.shop import resale_price
from app.logic.ship.parts import PARTS

from .harness import Scenario

scenario = Scenario('hangar')
check = scenario.check
remembered: dict[str, int] = {}             # from a step to a later one


def hangar() -> Any:
    return scenario.base.ids.hangar


def rows() -> dict[str | None, Any]:
    return {row.part: row for row in hangar().ids.parts.children}


def slot(slot_id: str) -> Any:
    return next(
        button for button in hangar().ids.slots.children
        if button.slot == slot_id
    )


@scenario.step(1.)
def opens() -> None:
    scenario.press(scenario.base.ids.hangar_button)


@scenario.step(.4)
def nothing_affordable() -> None:
    check(scenario.base.panel == 'hangar', 'the hangar opens')
    check(
        not any(row.can_act for row in rows().values()),
        'nothing to do without credits',
    )
    check('heavy_laser' not in rows(), 'higher tiers are hidden')
    base = scenario.base
    base.wallet.earn(30000)
    base.board.validated = TIER_MISSIONS[-1]
    base.depot.stock.update({'copper': 10., 'crystal': 3.})
    hangar().refresh()


@scenario.step(.3)
def buys_a_laser() -> None:
    scenario.press(scenario.button(rows()['laser'], 'Acheter'))


@scenario.step(.3)
def buys_a_heavy_laser() -> None:
    check(scenario.player.design.parts == {'nose': 'laser'},
          'a part bought is fitted')
    check(scenario.base.wallet.credits == 30000 - PARTS['laser'].price,
          'the laser is paid')
    scenario.press(scenario.button(rows()['heavy_laser'], 'Acheter'))


@scenario.step(.3)
def sells_the_laser() -> None:
    base = scenario.base
    check(base.depot.stock.get('copper', 0.) == 0., 'its ore is taken')
    check(base.inventory.spares == {'laser': 1},
          'the part taken off goes to the hangar')
    laser = rows()['laser']
    check(str(resale_price(PARTS['laser'])) in laser.resale.replace(' ', ''),
          'it sells back for less')
    remembered['credits'] = scenario.base.wallet.credits
    scenario.press(scenario.button(laser, laser.resale))


@scenario.step(.3)
def sold_back() -> None:
    base = scenario.base
    check(base.inventory.spares == {}, 'the laser is sold')
    check(base.wallet.credits == remembered['credits']
          + resale_price(PARTS['laser']), 'and paid back')
    # Down the list, which scrolls
    hangar().ids.parts.parent.scroll_to(rows()['quantum_laser'], animate=False)


@scenario.step(.3)
def picks_the_quantum_laser() -> None:
    row = rows()['quantum_laser']
    # On its name, not on its buttons
    scenario.press(row, at=(row.x + 30, row.center_y))


@scenario.step(.3)
def shows_the_change() -> None:
    stats = {row.name: row for row in hangar().ids.stats.children}
    check(stats['Laser'].change == 'up', 'a better laser shows up')
    check(stats['Vitesse'].change == 'down', 'a slower ship shows down')
    check(not rows()['quantum_laser'].can_act,
          'the quantum laser lacks ore')
    scenario.press(slot('left').children[0])


@scenario.step(.3)
def fits_fins_on_the_left() -> None:
    scenario.press(scenario.button(rows()['fins'], 'Acheter'))


@scenario.step(.3)
def the_right_side_takes_another() -> None:
    scenario.press(slot('right').children[0])


@scenario.step(.3)
def closes() -> None:
    check(rows()['fins'].action == 'buy', 'each side takes its own part')
    scenario.escape()
    scenario.base.depot.stock.update({'iron': 25., 'gold': 3.})


@scenario.step(.3)
def opens_the_market() -> None:
    check(scenario.base.panel == '', 'escape closes the hangar')
    scenario.press(scenario.base.ids.market_button)


@scenario.step(.4)
def sells_ten_iron() -> None:
    market = scenario.base.ids.market
    iron = next(r for r in market.ids.rows.children if r.mineral == 'iron')
    remembered['credits'] = scenario.base.wallet.credits
    scenario.press(scenario.button(iron, 'Vendre 10'))


@scenario.step(.3)
def sells_the_gold() -> None:
    base = scenario.base
    check(base.depot.stock['iron'] == 15., 'ten iron are sold')
    check(base.wallet.credits == remembered['credits']
          + 10 * ore_price('iron'),
          'the market pays for them')
    market = base.ids.market
    gold = next(r for r in market.ids.rows.children if r.mineral == 'gold')
    scenario.press(scenario.button(gold, 'Tout vendre'))


@scenario.step(.3)
def sold_out() -> None:
    check('gold' not in scenario.base.depot.stock, 'all the gold is sold')


scenario.run()
