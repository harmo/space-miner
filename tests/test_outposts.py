from app.logic.base.outposts import (
    CERES,
    DEPOT,
    FRONTIER,
    FUEL,
    TRADE,
    Construction,
    unlocked,
)
from app.logic.base.post import Services
from app.logic.save import Progress


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
    assert offered == [FUEL, DEPOT, TRADE]
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
    again.restore(outpost.progress)
    assert again.progress == Progress(1, {'rock': 30, 'iron': 12})
    again.restore(Progress(99, {}))
    assert again.built == len(FRONTIER.stages)


def test_each_stage_tells_what_it_adds() -> None:
    first, second, third = FRONTIER.stages
    assert unlocked(first, Services()) == ['le plein']
    assert unlocked(second, FUEL) == ['un entrepôt']
    assert unlocked(third, DEPOT) == ['un marché', 'des missions']


def test_the_frontier_pays_more_for_ore_ice_most_of_all() -> None:
    trade = FRONTIER.trade
    assert trade.factor('iron') == trade.markup > 1
    assert trade.factor('ice') > trade.factor('iron')
    assert trade.bonus > 1 and trade.clients


def test_ceres_refines_but_gives_no_missions() -> None:
    assert FRONTIER.contracts and not CERES.contracts
    assert CERES.stages[-1].services.refinery
    assert CERES.pad < FRONTIER.pad
