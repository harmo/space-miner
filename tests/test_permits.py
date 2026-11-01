from random import Random

from app.logic.base.board import Board
from app.logic.base.outposts import Construction
from app.logic.base.permits import Permits
from app.logic.base.post import Services
from app.logic.base.sites import (
    ARES,
    ARES_MINE,
    CERES,
    FRONTIER,
    FRONTIER_MINE,
    ICARE,
    PERMITS,
)
from app.logic.base.wallet import Wallet


def full(permit_wanted: dict[str, int]) -> dict[str, float]:
    return {name: float(units) for name, units in permit_wanted.items()}


def built_up_to_the_lock(permits: Permits) -> Construction:
    """ Ares, its depot built, its mine next """
    construction = Construction(ARES, permits)
    for stage in ARES.stages[:2]:
        construction.deliver(full(dict(stage.materials)))
    return construction


def test_mines_refineries_and_markets_take_a_concession() -> None:
    for site in (ARES, CERES, FRONTIER, ICARE):
        before = Services()
        for stage in site.stages:
            services = stage.services
            worth_it = (
                (services.mine and not before.mine)
                or (services.refinery and not before.refinery)
                or (services.market and not before.market)
            )
            assert bool(stage.permit) == bool(worth_it), stage.name
            before = services


def test_foundations_and_depots_need_none() -> None:
    for site in (ARES, CERES, FRONTIER, ICARE):
        assert site.stages[0].permit is None
        assert site.stages[1].permit is None


def test_a_stage_stays_locked_without_its_concession() -> None:
    construction = built_up_to_the_lock(Permits())
    assert construction.locked
    stage = construction.stage
    assert stage is not None
    cargo = full(dict(stage.materials))
    before = dict(cargo)
    assert construction.deliver(cargo) is None
    assert cargo == before and construction.delivered == {}


def test_a_concession_opens_the_stage() -> None:
    permits = Permits()
    construction = built_up_to_the_lock(permits)
    permits.granted.add(ARES_MINE.key)
    assert not construction.locked
    stage = construction.stage
    assert stage is not None
    assert construction.deliver(full(dict(stage.materials))) is stage


def test_concessions_come_with_the_reputation() -> None:
    permits = Permits()
    assert permits.offered(PERMITS, 1) == []
    assert ARES_MINE in permits.offered(PERMITS, 2)
    assert FRONTIER_MINE not in permits.offered(PERMITS, 3)
    assert FRONTIER_MINE in permits.offered(PERMITS, 4)


def test_validating_takes_the_ore_pays_and_grants() -> None:
    permits = Permits()
    wallet = Wallet()
    board = Board(Random(1), wallet)
    stock = full(ARES_MINE.mission.wanted)
    permits.validate(ARES_MINE, board, stock)
    assert not stock
    assert wallet.credits == ARES_MINE.mission.reward
    assert board.validated == 1
    assert not permits.lacks(ARES_MINE)
    assert ARES_MINE not in permits.offered(PERMITS, 5)


def test_nothing_happens_without_the_ore() -> None:
    permits = Permits()
    wallet = Wallet()
    board = Board(Random(2), wallet)
    stock = {'iron': 5.}
    permits.validate(ARES_MINE, board, stock)
    assert stock == {'iron': 5.} and wallet.credits == 0
    assert permits.lacks(ARES_MINE)


def test_a_concession_counts_once() -> None:
    permits = Permits()
    board = Board(Random(3), Wallet())
    wanted = ARES_MINE.mission.wanted
    permits.validate(ARES_MINE, board, full(wanted))
    permits.validate(ARES_MINE, board, full(wanted))
    assert board.validated == 1


def test_concessions_are_much_bigger_than_missions() -> None:
    for permit in PERMITS:
        assert sum(permit.mission.wanted.values()) >= 100
