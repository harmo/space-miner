import math

import pytest

from app.logic.ship.config import LEG_DEPLOY_TIME, LEG_LENGTH
from app.logic.ship.ground import landed_on
from app.logic.ship.legs import legs, unfold
from app.logic.world.space import Celestial

SIZE = (40., 25.)


def planet() -> Celestial:
    return Celestial(0, 200., pos=(0., 0.))


def test_unfolded_legs_stand_on_the_ground() -> None:
    ground = planet()
    direction = math.radians(30)
    pos = landed_on(ground, direction, SIZE[0])
    for hip, foot in legs(pos, direction, SIZE, 1., ground):
        assert math.dist(foot, ground.pos) == pytest.approx(
            ground.radius, abs=1.
        )
        assert math.dist(hip, ground.pos) > ground.radius + LEG_LENGTH


def test_legs_spread_on_both_sides() -> None:
    (_, left), (_, right) = legs((0., 1000.), 0., SIZE, 1., planet())
    assert left[1] > 1000. + SIZE[1] / 2 > 1000. - SIZE[1] / 2 > right[1]
    assert left[0] < -SIZE[0] / 2 and right[0] < -SIZE[0] / 2


def test_folded_legs_stay_along_the_hull() -> None:
    for _, foot in legs((0., 1000.), 0., SIZE, 0., planet()):
        assert foot[0] == pytest.approx(-SIZE[0] / 2)
        assert abs(foot[1] - 1000.) < SIZE[1] / 2


def test_legs_never_go_into_the_ground() -> None:
    ground = planet()
    # Lying on its side, close to the ground
    pos = (0., ground.radius + SIZE[1] / 2 + 1.)
    for _, foot in legs(pos, 0., SIZE, 1., ground):
        assert math.dist(foot, ground.pos) >= ground.radius - 1e-6


def test_legs_unfold_and_fold_over_time() -> None:
    half = unfold(0., LEG_DEPLOY_TIME / 2, out=True)
    assert half == pytest.approx(.5)
    assert unfold(half, LEG_DEPLOY_TIME, out=True) == 1.
    assert unfold(half, LEG_DEPLOY_TIME, out=False) == 0.
