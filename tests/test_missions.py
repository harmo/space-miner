from random import Random

import pytest

from app.logic.base.board import Board, Contracts
from app.logic.base.config import (
    MISSION_OFFERS,
    MISSION_REFILL,
    MISSIONS_ACTIVE,
    TIER_MISSIONS,
)
from app.logic.base.market import ore_value
from app.logic.base.missions import (
    Clientele,
    Desk,
    Mission,
    Need,
    make_mission,
    make_order,
    needs,
    needs_at,
)
from app.logic.base.wallet import Wallet
from app.logic.mining.minerals import MINERALS


def test_missions_want_a_few_rare_minerals() -> None:
    rng = Random(1)
    for _ in range(200):
        mission = make_mission(rng)
        assert 1 <= len(mission.wanted) <= 2
        assert 'rock' not in mission.wanted and 'ice' not in mission.wanted
        assert all(units >= 2 for units in mission.wanted.values())
        assert mission.reward > 0 and mission.reward % 10 == 0


def test_rarer_minerals_are_wanted_in_smaller_amounts() -> None:
    rng = Random(2)
    amounts: dict[str, list[int]] = {}
    for _ in range(2000):
        for name, units in make_mission(rng, 5).wanted.items():
            amounts.setdefault(name, []).append(units)
    def mean(name: str) -> float:
        return sum(amounts[name]) / len(amounts[name])
    assert mean('iron') > mean('gold') > mean('antimatter')


MISSION = Mission('Test', {'iron': 10, 'gold': 2}, 300)


def test_missing_ore() -> None:
    assert MISSION.missing({'iron': 4.5}) == {'iron': 6, 'gold': 2}
    assert MISSION.missing({'iron': 12., 'gold': 1.9999999}) == {}
    assert MISSION.can_validate({'iron': 10., 'gold': 2.})


def test_two_missions_at_a_time_at_first() -> None:
    board = Board(Random(3), Wallet())
    assert len(board.offers) == MISSION_OFFERS[0]
    assert board.most == MISSIONS_ACTIVE[0] == 2
    for _ in range(board.most):
        board.accept(board.offers[0])
    assert board.full
    offers = list(board.offers)
    board.accept(board.offers[0])
    assert len(board.active) == board.most
    assert board.offers == offers


def test_more_missions_with_more_reputation() -> None:
    board = Board(Random(3), Wallet())
    board.validated = TIER_MISSIONS[-1] - 1
    mission = Mission('Test', {'iron': 2}, 10)
    board.offers[0] = mission
    board.accept(mission)
    board.validate(mission, {'iron': 2.})
    assert board.most == MISSIONS_ACTIVE[-1] == 8
    assert board.room == MISSION_OFFERS[-1] == 8
    assert MISSIONS_ACTIVE == tuple(sorted(MISSIONS_ACTIVE))
    assert MISSION_OFFERS == tuple(sorted(MISSION_OFFERS))


def test_validating_takes_the_ore_and_pays() -> None:
    board = Board(Random(5), Wallet())
    board.offers[0] = MISSION
    board.accept(MISSION)
    stock = {'iron': 12., 'gold': 2.}
    board.validate(MISSION, stock)
    assert stock == {'iron': 2.}
    assert board.wallet.credits == 300
    assert board.active == []


def test_validating_needs_the_ore() -> None:
    board = Board(Random(6), Wallet())
    board.offers[0] = MISSION
    board.accept(MISSION)
    stock = {'iron': 12.}
    board.validate(MISSION, stock)
    assert stock == {'iron': 12.}
    assert board.wallet.credits == 0
    assert board.active == [MISSION]


def test_abandon() -> None:
    board = Board(Random(7), Wallet())
    mission = board.offers[0]
    board.accept(mission)
    board.abandon(mission)
    assert board.active == [] and board.wallet.credits == 0


def test_needs_add_up_the_missions() -> None:
    first = Mission('A', {'gold': 4, 'iron': 10}, 100)
    second = Mission('B', {'iron': 5}, 100)
    cargo, stock = {'iron': 3.5}, {'iron': 6., 'gold': 4.}
    assert needs([first, second], cargo, stock) == [
        Need('iron', 9, 15), Need('gold', 4, 4),
    ]
    assert [need.met for need in needs([first], cargo, stock)] == [
        False, True,
    ]
    assert needs([], cargo, stock) == []


def test_validating_from_the_depot_then_the_cargo() -> None:
    board = Board(Random(8), Wallet())
    board.offers[0] = MISSION
    board.accept(MISSION)
    depot, cargo = {'iron': 4.5}, {'iron': 6., 'gold': 2.5}
    assert MISSION.missing(depot) == {'iron': 6, 'gold': 2}
    assert MISSION.can_validate(depot, cargo)
    board.validate(MISSION, depot, cargo)
    assert depot == {}
    assert cargo == pytest.approx({'iron': .5, 'gold': .5})
    assert board.wallet.credits == MISSION.reward


def board_at(validated: int) -> Board:
    board = Board(Random(9), Wallet())
    board.validated = validated
    return board


def validate_one(board: Board) -> None:
    mission = Mission('Test', {'iron': 2}, 10)
    board.offers[0] = mission
    board.accept(mission)
    board.validate(mission, {'iron': 2.})


def test_levels_go_up_to_the_reputation() -> None:
    board = board_at(TIER_MISSIONS[2])          # third tier
    board.choose_level(5)
    assert board.level == 3
    assert all(mission.level == 3 for mission in board.offers)
    board.choose_level(1)
    assert all(mission.level == 1 for mission in board.offers)
    assert board.room == MISSION_OFFERS[2]


def test_at_the_top_missions_stay_at_the_top() -> None:
    board = board_at(TIER_MISSIONS[1] - 1)
    validate_one(board)                        # reaches the second tier
    assert board.level == 2
    assert all(mission.level == 2 for mission in board.offers[1:])


def test_a_lower_level_chosen_stays() -> None:
    board = board_at(TIER_MISSIONS[2] - 1)
    board.choose_level(1)
    validate_one(board)
    assert board.level == 1


def test_higher_levels_want_rarer_minerals() -> None:
    def rare_share(level: int) -> float:
        rng = Random(10)
        wanted = [
            name for _ in range(1000)
            for name in make_mission(rng, level).wanted
        ]
        rare = [name for name in wanted if MINERALS[name].laser >= 3]
        return len(rare) / len(wanted)
    assert rare_share(5) > 2 * rare_share(1)


def test_local_clients_pay_more() -> None:
    plain = make_mission(Random(7))
    local = make_mission(Random(7), clients=('Colonie',), bonus=1.25)
    assert local.client == 'Colonie' and local.wanted == plain.wanted
    assert local.reward == pytest.approx(plain.reward * 1.25, abs=10)


def test_each_board_makes_its_own_reputation() -> None:
    wallet = Wallet()
    earth = Board(Random(8), wallet)
    outpost = Board(
        Random(9), wallet, clientele=Clientele(('Colonie',), 1.25),
    )
    mission = outpost.offers[0]
    outpost.accept(mission)
    stock = {name: float(units) for name, units in mission.wanted.items()}
    outpost.validate(mission, stock)
    assert outpost.validated == 1 and earth.validated == 0
    assert wallet.credits == mission.reward


def test_needs_add_up_across_desks_each_with_its_depot() -> None:
    earth = Desk([Mission('Institut Cassini', {'iron': 10}, 100)],
                 {'iron': 3., 'gold': 9.})
    outpost = Desk([Mission('Colonie Thulé', {'iron': 5, 'ruby': 2}, 100)],
                   {'iron': 4.})
    assert needs_at([earth, outpost], {'iron': 1.}) == [
        Need('iron', 8, 15), Need('ruby', 0, 2),
    ]


def test_a_depot_only_counts_for_what_its_desk_wants() -> None:
    earth = Desk([Mission('Institut Cassini', {'iron': 10}, 100)],
                 {'gold': 9.})
    outpost = Desk([Mission('Colonie Thulé', {'gold': 5}, 100)], {'iron': 4.})
    assert needs_at([earth, outpost], {}) == [
        Need('iron', 0, 10), Need('gold', 0, 5),
    ]


def test_a_board_resumes_its_contracts() -> None:
    board = Board(Random(10), Wallet())
    mission = board.offers[0]
    board.accept(mission)
    contracts = board.contracts
    other = Board(Random(11), Wallet())
    other.resume(contracts)
    assert other.active == [mission]
    assert other.offers == board.offers
    assert other.contracts == contracts


def test_a_board_resumes_at_a_level_its_reputation_allows() -> None:
    board = Board(Random(12), Wallet())
    board.resume(Contracts(level=4))
    assert board.level == 1
    assert len(board.offers) > 0


ORDERS = Clientele(('Chantier',), 1.5, (('rock', 120), ('regolith', 60)))


def test_building_sites_order_common_ore_by_the_shipload() -> None:
    board = Board(Random(20), Wallet(), clientele=ORDERS)
    for mission in board.offers:
        assert mission.client == 'Chantier'
        assert set(mission.wanted) <= {'rock', 'regolith'}
        assert sum(mission.wanted.values()) >= 20


def test_bigger_orders_on_higher_levels() -> None:
    def total(level: int) -> int:
        rng = Random(21)
        return sum(
            sum(make_order(rng, level, ORDERS).wanted.values())
            for _ in range(200)
        )
    assert total(4) > total(1) * 1.5


def test_orders_pay_more_than_the_ore_is_worth() -> None:
    mission = make_order(Random(22), 1, ORDERS)
    value = sum(
        units * ore_value(MINERALS[name])
        for name, units in mission.wanted.items()
    )
    assert mission.reward >= value


def test_an_order_is_validated_from_the_depot_and_the_cargo() -> None:
    wallet = Wallet()
    board = Board(Random(23), wallet, clientele=ORDERS)
    mission = board.offers[0]
    board.accept(mission)
    stock = {name: float(units) for name, units in mission.wanted.items()}
    board.validate(mission, stock)
    assert wallet.credits == mission.reward and not stock


@pytest.mark.parametrize('level', [1, 2, 3, 4, 5])
def test_a_mission_only_wants_what_its_level_can_mine(level: int) -> None:
    rng = Random(30 + level)
    for _ in range(300):
        mission = make_mission(rng, level)
        assert all(MINERALS[name].laser <= level for name in mission.wanted)


def test_all_ore_is_wanted_at_the_top_level() -> None:
    rng = Random(36)
    wanted = {
        name for _ in range(2000) for name in make_mission(rng, 5).wanted
    }
    assert 'antimatter' in wanted and 'ruby' in wanted


def test_higher_levels_pay_much_more() -> None:
    def average(level: int) -> float:
        rng = Random(37)
        return sum(make_mission(rng, level).reward for _ in range(2000)) / 2000
    assert average(5) > 5 * average(1)
    rewards = [average(level) for level in range(1, 6)]
    assert rewards == sorted(rewards)


def test_higher_levels_ask_for_more() -> None:
    def units(level: int) -> float:
        rng = Random(38)
        return sum(
            sum(make_mission(rng, level).wanted.values())
            for _ in range(2000)
        ) / 2000
    assert units(5) > 1.5 * units(1)


def test_an_offer_taken_is_not_replaced_at_once() -> None:
    board = Board(Random(40), Wallet())
    count = len(board.offers)
    board.accept(board.offers[0])
    assert len(board.offers) == count - 1
    assert board.next_offer == MISSION_REFILL


def test_it_comes_back_after_a_while() -> None:
    board = Board(Random(41), Wallet())
    count = len(board.offers)
    board.accept(board.offers[0])
    board.update(MISSION_REFILL - 1.)
    assert len(board.offers) == count - 1
    assert board.next_offer == pytest.approx(1.)
    board.update(2.)
    assert len(board.offers) == count
    assert board.next_offer is None


def test_offers_come_back_one_at_a_time() -> None:
    board = Board(Random(42), Wallet())
    count = len(board.offers)
    board.accept(board.offers[0])
    board.accept(board.offers[0])
    board.update(MISSION_REFILL + 1.)
    assert len(board.offers) == count - 1
    assert board.next_offer is not None


def test_looking_at_another_level_gives_no_new_offers() -> None:
    board = Board(Random(43), Wallet())
    board.validated = 3
    before = list(board.offers)
    board.choose_level(2)
    assert all(mission.level == 2 for mission in board.offers)
    board.choose_level(1)
    assert board.offers == before


def test_each_level_recharges_on_its_own() -> None:
    board = Board(Random(44), Wallet())
    board.validated = 8
    board.choose_level(2)
    board.accept(board.offers[0])
    level_two = len(board.offers)
    board.update(100.)
    board.choose_level(3)
    board.accept(board.offers[0])
    level_three = len(board.offers)
    board.update(MISSION_REFILL - 99.)
    assert len(board.shelf(2)) == level_two + 1
    assert len(board.shelf(3)) == level_three


def test_offers_recharge_while_looking_elsewhere() -> None:
    board = Board(Random(45), Wallet())
    board.validated = 3
    board.accept(board.offers[0])
    left = len(board.offers)
    board.choose_level(2)
    board.update(MISSION_REFILL + 1.)
    assert len(board.shelf(1)) == left + 1


def test_a_better_reputation_brings_room_for_more_in_time() -> None:
    board = Board(Random(46), Wallet())
    count = len(board.offers)
    board.validated = 3
    assert board.room > count and len(board.offers) == count
    board.update(MISSION_REFILL + 1.)
    assert len(board.offers) == count + 1


def test_what_is_recharging_comes_back_saved() -> None:
    board = Board(Random(47), Wallet())
    board.accept(board.offers[0])
    board.update(30.)
    contracts = board.contracts
    other = Board(Random(48), Wallet())
    other.resume(contracts)
    assert other.offers == board.offers
    assert other.next_offer == pytest.approx(MISSION_REFILL - 30.)
