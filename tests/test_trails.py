import math
from random import Random

import pytest

from app.logic.ship.config import TRAIL_MAX
from app.logic.ship.parts import PARTS
from app.logic.ship.shipyard import Design, ship_size
from app.logic.ship.trails import NOZZLE, TRAILS, Trail, look, nozzles

DT = 1 / 60


def test_a_bare_hull_has_its_own_nozzle_at_the_back() -> None:
    [((x, y), style)] = nozzles(Design())
    assert style == NOZZLE
    assert x == pytest.approx(-ship_size(Design()).length / 2)
    assert y == pytest.approx(0.)


def test_an_engine_moves_the_nozzle_back() -> None:
    design = Design(parts={'rear': 'engine'})
    [((x, _), style)] = nozzles(design)
    assert style == 'engine'
    assert x == pytest.approx(-ship_size(design).length / 2)


def test_some_engines_have_two_nozzles() -> None:
    twin = nozzles(Design(parts={'rear': 'twin_engine'}))
    assert [style for _, style in twin] == ['twin_engine', 'twin_engine']
    assert twin[0][0][1] == pytest.approx(-twin[1][0][1])


def test_two_rear_slots_two_trails() -> None:
    cruiser = Design('cruiser', {'rear_left': 'ion_engine'})
    assert sorted(style for _, style in nozzles(cruiser)) == [
        NOZZLE, 'ion_engine',
    ]


def test_a_cargo_hold_behind_throws_what_the_hull_does() -> None:
    [(_, style)] = nozzles(Design(parts={'rear': 'rear_hold'}))
    assert style == NOZZLE


def test_every_engine_has_its_trail() -> None:
    engines = {
        part_id for part_id, part in PARTS.items()
        if part.kind == 'rear' and part.thrust + part.max_speed > 0
    }
    assert engines <= set(TRAILS)


def fly(trail: Trail, seconds: float, thrust: float = 1.) -> None:
    for _ in range(round(seconds / DT)):
        trail.update(DT, (0., 0.), 0., (100., 0.),
                     nozzles(Design(parts={'rear': 'engine'})), thrust)


def test_sparks_fly_backwards_from_the_ship() -> None:
    trail = Trail(Random(0))
    fly(trail, .2)
    style = TRAILS['engine']
    assert len(trail.sparks) == pytest.approx(style.rate * .2, abs=2)
    for spark in trail.sparks:
        # The ship moves at 100 px/s along +x, sparks go back from it
        assert spark.vx < 100 - style.speed * .6
        assert abs(math.degrees(math.atan2(spark.vy, spark.vx - 100))) > (
            180 - style.spread
        )


def test_no_thrust_no_sparks_and_old_ones_fade_out() -> None:
    trail = Trail(Random(0))
    fly(trail, .2)
    fly(trail, TRAILS['engine'].life + .1, thrust=0.)
    assert trail.sparks == []


def test_less_thrust_fewer_sparks() -> None:
    full, weak = Trail(Random(0)), Trail(Random(0))
    fly(full, .5)
    fly(weak, .5, thrust=.3)
    assert len(weak.sparks) < len(full.sparks) / 2


def test_sparks_are_bounded() -> None:
    trail = Trail(Random(0))
    for _ in range(100):
        trail.update(DT, (0., 0.), 0., (0., 0.),
                     nozzles(Design(parts={'rear': 'engine'})) * 40, 1.)
    assert len(trail.sparks) <= TRAIL_MAX


def test_sparks_fade_and_shrink() -> None:
    trail = Trail(Random(0))
    fly(trail, DT)
    spark = trail.sparks[0]
    color, alpha, size = look(spark)
    spark.age = spark.style.life * .9
    old_color, old_alpha, old_size = look(spark)
    assert old_alpha < alpha and old_size < size
    assert old_color == pytest.approx(spark.style.end, abs=.15)


def test_sparks_follow_world_shifts() -> None:
    trail = Trail(Random(0))
    fly(trail, .1)
    before = [spark.x for spark in trail.sparks]
    trail.shift((1000., 0.))
    after = [spark.x - 1000. for spark in trail.sparks]
    assert after == pytest.approx(before)
