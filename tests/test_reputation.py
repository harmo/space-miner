from random import Random

from app.logic.base.config import TIER_MISSIONS
from app.logic.base.missions import Board, Mission, make_mission
from app.logic.base.reputation import is_sold, next_tier, tier
from app.logic.base.wallet import Wallet
from app.logic.ship.parts import PARTS


def test_tiers_are_reached_with_missions() -> None:
    assert tier(0) == 1
    assert tier(TIER_MISSIONS[1] - 1) == 1
    assert tier(TIER_MISSIONS[1]) == 2
    assert tier(10_000) == len(TIER_MISSIONS)


def test_next_tier() -> None:
    assert next_tier(0) == (2, TIER_MISSIONS[1])
    assert next_tier(TIER_MISSIONS[-1]) is None


def test_only_the_first_tier_is_sold_at_first() -> None:
    sold = [part for part in PARTS.values() if is_sold(part, 0)]
    assert sold and all(part.tier == 1 for part in sold)
    assert len(sold) < len(PARTS) / 3
    assert all(is_sold(part, TIER_MISSIONS[-1]) for part in PARTS.values())


def test_each_slot_has_something_to_buy_at_first() -> None:
    first = {part.kind for part in PARTS.values() if part.tier == 1}
    assert first == {'nose', 'rear', 'side', 'internal'}


def test_validated_missions_make_the_reputation() -> None:
    board = Board(Random(1), Wallet())
    mission = Mission('Test', {'iron': 2}, 100)
    board.offers[0] = mission
    board.accept(mission)
    board.validate(mission, {'iron': 5.})
    assert board.validated == 1
    board.abandon(board.offers[0])
    assert board.validated == 1


def test_clients_order_more_at_higher_tiers() -> None:
    def mean_reward(level: int) -> float:
        rng = Random(3)
        rewards = [make_mission(rng, level).reward for _ in range(500)]
        return sum(rewards) / len(rewards)
    assert mean_reward(5) > 1.8 * mean_reward(1)
