from random import Random

import pytest

from app.logic.base.config import (
    MISSION_OFFERS,
    MISSIONS_ACTIVE,
    TIER_MISSIONS,
)
from app.logic.base.missions import (
    Board,
    Contracts,
    Desk,
    Mission,
    Need,
    make_mission,
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
        for name, units in make_mission(rng).wanted.items():
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
    assert len(board.offers) == MISSION_OFFERS[-1] == 8
    assert MISSIONS_ACTIVE == tuple(sorted(MISSIONS_ACTIVE))
    assert MISSION_OFFERS == tuple(sorted(MISSION_OFFERS))


def test_accepted_offer_is_replaced() -> None:
    board = Board(Random(4), Wallet())
    taken = board.offers[1]
    board.accept(taken)
    assert board.active == [taken]
    assert len(board.offers) == MISSION_OFFERS[0]


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
    assert len(board.offers) == MISSION_OFFERS[2]


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


def test_boards_share_the_reputation_they_make() -> None:
    wallet = Wallet()
    earth = Board(Random(8), wallet)
    outpost = Board(Random(9), wallet, earth.standing, ('Colonie',), 1.25)
    mission = outpost.offers[0]
    outpost.accept(mission)
    stock = {name: float(units) for name, units in mission.wanted.items()}
    outpost.validate(mission, stock)
    assert outpost.validated == earth.validated == 1
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
