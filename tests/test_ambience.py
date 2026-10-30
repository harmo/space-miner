import math
from random import Random

import pytest

from app.logic.ambience import (
    CALL_EVERY,
    CALLS,
    DRONE_FADE,
    DRONE_HOLD,
    DRONES,
    Ambience,
)


def faded_in(ambience: Ambience) -> None:
    """ Up to the start of the fade """
    ambience.update(ambience.alone)


def test_a_drone_plays_alone_at_first() -> None:
    ambience = Ambience(Random(1))
    assert ambience.volumes == {ambience.current: 1.}
    assert DRONE_HOLD[0] <= ambience.alone <= DRONE_HOLD[1]
    assert ambience.upcoming != ambience.current


def test_it_fades_into_the_next_one() -> None:
    ambience = Ambience(Random(2))
    current, upcoming = ambience.current, ambience.upcoming
    faded_in(ambience)
    ambience.update(DRONE_FADE / 2)
    volumes = ambience.volumes
    assert volumes[current] == pytest.approx(volumes[upcoming])
    assert sum(v * v for v in volumes.values()) == pytest.approx(1.)


def test_then_plays_it_alone_and_picks_another() -> None:
    ambience = Ambience(Random(3))
    upcoming = ambience.upcoming
    faded_in(ambience)
    ambience.update(DRONE_FADE)
    assert ambience.volumes == {upcoming: 1.}
    assert ambience.upcoming not in (upcoming, None)


def test_every_drone_comes_in_time() -> None:
    ambience = Ambience(Random(4))
    heard = {ambience.current}
    for _ in range(100):
        faded_in(ambience)
        ambience.update(DRONE_FADE)
        heard.add(ambience.current)
    assert heard == set(DRONES)


def test_radio_calls_now_and_then() -> None:
    ambience = Ambience(Random(5))
    assert ambience.call(CALL_EVERY[0] / 2) is None
    calls = [ambience.call(CALL_EVERY[1]) for _ in range(50)]
    assert all(call in CALLS for call in calls)
    assert len(set(calls)) > 1


def test_drones_fade_smoothly() -> None:
    ambience = Ambience(Random(6))
    current = ambience.current
    faded_in(ambience)
    levels = []
    for _ in range(12):
        ambience.update(DRONE_FADE / 12)
        levels.append(ambience.volumes.get(current, 0.))
    assert levels == sorted(levels, reverse=True)
    assert not math.isclose(levels[0], 1.)
