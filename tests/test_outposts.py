import math
from random import Random

from app.logic.base.board import Board, Contracts
from app.logic.base.config import PAD_DIRECTION
from app.logic.base.outposts import (
    Construction,
    Outpost,
    Progress,
    bare_outpost,
    open_boards,
)
from app.logic.base.post import Services
from app.logic.base.sites import (
    CERES,
    DEPOT,
    FRONTIER,
    FUEL,
    ICARE,
    MINING,
    TRADING_POST,
    unlocked,
)
from app.logic.base.wallet import Wallet
from app.logic.ship.parking import parking_on
from app.logic.world.space import Celestial


def test_an_outpost_starts_as_a_bare_site() -> None:
    outpost = Construction(FRONTIER)
    assert outpost.built == 0 and outpost.stage is FRONTIER.stages[0]
    assert outpost.services == Services()
    assert outpost.needed == dict(FRONTIER.stages[0].materials)


def test_ore_is_delivered_from_the_cargo_as_far_as_needed() -> None:
    outpost = Construction(FRONTIER)
    cargo = {'rock': 30.5, 'iron': 10.}
    assert outpost.deliver(cargo) is None
    assert cargo == {'rock': .5, 'iron': 10.}
    assert outpost.needed == {'rock': 120 - 30}


def test_a_stage_is_built_once_all_is_delivered() -> None:
    outpost = Construction(FRONTIER)
    cargo = {'rock': 200.}
    built = outpost.deliver(cargo)
    assert built is FRONTIER.stages[0]
    assert outpost.built == 1 and outpost.services == FUEL
    assert cargo == {'rock': 80.}, 'the rest kept for the next stage'
    assert outpost.delivered == {}


def test_each_stage_offers_more() -> None:
    outpost = Construction(FRONTIER)
    offered = []
    for stage in FRONTIER.stages:
        outpost.deliver({name: float(units) for name, units in
                         stage.materials})
        offered.append(outpost.services)
    assert offered == [FUEL, DEPOT, TRADING_POST, MINING]
    assert outpost.stage is None and outpost.needed == {}
    assert outpost.deliver({'rock': 50.}) is None


def test_nothing_is_taken_that_is_not_needed() -> None:
    outpost = Construction(FRONTIER)
    cargo = {'gold': 5.}
    outpost.deliver(cargo)
    assert cargo == {'gold': 5.} and outpost.delivered == {}


def test_how_far_it_was_built_comes_back() -> None:
    outpost = Construction(FRONTIER)
    cargo = {'rock': 150., 'iron': 12.}
    outpost.deliver(cargo)
    outpost.deliver(cargo)
    again = Construction(FRONTIER)
    again.restore(Progress(outpost.built, outpost.delivered))
    assert again.built == 1
    assert again.delivered == {'rock': 30, 'iron': 12}
    again.restore(Progress(99, {}))
    assert again.built == len(FRONTIER.stages)


def test_each_stage_tells_what_it_adds() -> None:
    first, second, third, fourth = FRONTIER.stages
    assert unlocked(first, Services()) == ['le plein']
    assert unlocked(second, FUEL) == ['un entrepôt']
    assert unlocked(third, DEPOT) == ['un marché', 'des missions']
    assert unlocked(fourth, TRADING_POST) == ['une mine']


def test_the_frontier_pays_more_for_ore_ice_most_of_all() -> None:
    trade = FRONTIER.trade
    assert trade.factor('iron') == trade.markup > 1
    assert trade.factor('ice') > trade.factor('iron')
    assert trade.clientele.bonus > 1 and trade.clientele.clients


def test_ceres_refines_and_orders_common_ore() -> None:
    assert FRONTIER.gives_missions and CERES.gives_missions
    assert CERES.trade.clientele.orders and not FRONTIER.trade.clientele.orders
    assert CERES.stages[-1].services.refinery
    assert CERES.pad_width < FRONTIER.pad_width


def test_icare_shelters_and_buys_ejecta_dearer() -> None:
    assert ICARE.form == 'orbit' and not ICARE.gives_missions
    assert ICARE.stages[0].services.shelter
    assert ICARE.trade.factor('antimatter') > 1.5
    assert ICARE.trade.factor('iron') == 1.


def outpost_on(key: str) -> Outpost:
    return bare_outpost(key, Celestial(1, 200.), Random(1))


def test_an_outpost_offers_what_its_stages_built() -> None:
    outpost = outpost_on('frontier')
    assert outpost.post.services == Services()
    outpost.deliver({'rock': 120.})
    assert outpost.post.services == FUEL


def test_an_outpost_serves_ships_parked_on_its_pad_only() -> None:
    outpost = outpost_on('frontier')
    pad = math.radians(PAD_DIRECTION)
    parked = parking_on(outpost.body, pad, 40.)
    aside = parking_on(outpost.body, pad + math.pi, 40.)
    elsewhere = parking_on(Celestial(2, 200.), pad, 40.)
    assert outpost.serves(parked)
    assert not outpost.serves(aside)
    assert not outpost.serves(elsewhere)
    assert not outpost.serves(None)


def test_a_station_serves_ships_docked_at_its_port() -> None:
    station = outpost_on('icare')
    ground = station.ground
    assert ground.kind == 'port'
    assert ground.spots(60.) == [station.direction]
    assert station.serves(parking_on(station.body, station.direction, 60.))


def test_only_sites_giving_missions_open_a_board() -> None:
    outposts = [outpost_on('frontier'), outpost_on('icare')]
    open_boards(outposts, Wallet())
    assert isinstance(outposts[0].board, Board)
    assert outposts[1].board is None


def test_the_progress_of_an_outpost_comes_back() -> None:
    outpost = outpost_on('frontier')
    open_boards([outpost], Wallet())
    outpost.deliver({'rock': 150.})
    outpost.post.depot.stock['gold'] = 2.
    again = outpost_on('frontier')
    open_boards([again], Wallet())
    again.restore(outpost.progress)
    assert again.progress == outpost.progress
    assert again.post.services == FUEL
    assert again.progress.started


def test_an_outpost_without_board_has_no_contracts() -> None:
    assert outpost_on('icare').progress.contracts == Contracts()


def test_an_outpost_gets_its_reputation_back() -> None:
    outpost = outpost_on('frontier')
    open_boards([outpost], Wallet())
    assert outpost.board is not None
    outpost.board.validated = 5
    again = outpost_on('frontier')
    open_boards([again], Wallet())
    again.restore(outpost.progress)
    assert again.board is not None and again.board.validated == 5
