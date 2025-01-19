import math
from random import Random

import pytest

from app.logic.world.explosion import Explosion


def explosion(velocity: tuple[float, float] = (0., 0.)) -> Explosion:
    return Explosion(
        Random(0), (100., 200.), velocity, (1., 1., 1.),
        count=50, speed=(50., 100.), duration=1.,
    )


def test_fragments_fly_away_from_the_center() -> None:
    boom = explosion()
    boom.update(1.)
    for fragment in boom.fragments:
        distance = math.dist((fragment.x, fragment.y), (100., 200.))
        assert 50. <= distance <= 100.


def test_fragments_spread_in_all_directions() -> None:
    boom = explosion()
    boom.update(1.)
    angles = [math.atan2(f.y - 200., f.x - 100.) for f in boom.fragments]
    assert min(angles) < -math.pi / 2 and max(angles) > math.pi / 2


def test_fragments_move_along_with_the_velocity() -> None:
    boom = explosion(velocity=(300., 0.))
    boom.update(1.)
    mean_x = sum(f.x for f in boom.fragments) / len(boom.fragments)
    assert mean_x == pytest.approx(400., abs=30.)


def test_explosion_ends_after_its_duration() -> None:
    boom = explosion()
    boom.update(.5)
    assert boom.progress == pytest.approx(.5)
    assert not boom.done
    boom.update(.6)
    assert boom.progress == 1.
    assert boom.done


def test_fragments_follow_world_shifts() -> None:
    boom = explosion()
    boom.shift((36000., 0.))
    assert all(f.x == 36100. for f in boom.fragments)
