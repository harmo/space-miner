from app.logic.base.config import ORE_SALE
from app.logic.base.market import ore_price, ore_value, sell_ore
from app.logic.base.wallet import Wallet
from app.logic.mining.minerals import MINERALS


def test_rarer_and_harder_ore_is_worth_more() -> None:
    assert ore_value(MINERALS['gold']) > ore_value(MINERALS['iron'])
    assert ore_value(MINERALS['antimatter']) > ore_value(MINERALS['ruby'])
    assert ore_value(MINERALS['iron']) > ore_value(MINERALS['rock'])


def test_the_market_pays_less_than_the_ore_is_worth() -> None:
    for name, mineral in MINERALS.items():
        assert 1 <= ore_price(name) <= max(1, ore_value(mineral))
    assert ore_price('gold') == round(ore_value(MINERALS['gold']) * ORE_SALE)


def test_selling_ore_from_the_stock() -> None:
    wallet, stock = Wallet(), {'iron': 12.5, 'gold': 3.}
    assert sell_ore(stock, 'iron', 10, wallet) == 10
    assert stock['iron'] == 2.5
    assert wallet.credits == 10 * ore_price('iron')
    # Whole units only, and no more than there is
    assert sell_ore(stock, 'iron', 10, wallet) == 2
    assert stock == {'iron': .5, 'gold': 3.}
    assert sell_ore(stock, 'ruby', 5, wallet) == 0


def test_wallet() -> None:
    wallet = Wallet(50)
    wallet.earn(25)
    wallet.pay(70)
    assert wallet.credits == 5 and not wallet.can_pay(6)


def test_outposts_may_pay_more() -> None:
    assert ore_price('gold', 2.) == round(
        ore_value(MINERALS['gold']) * ORE_SALE * 2
    )
    wallet = Wallet()
    sell_ore({'iron': 10.}, 'iron', 10, wallet, factor=1.5)
    assert wallet.credits == 10 * ore_price('iron', 1.5)
