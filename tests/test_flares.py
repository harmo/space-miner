import math
from random import Random

import pytest

from app.logic.mining.minerals import MINERALS
from app.logic.world.config import (
    EJECTA_ASTEROIDS,
    EJECTA_ORBIT,
    EJECTA_STAYS,
    FLARE_BLAZE,
    FLARE_EVERY,
    FLARE_SURGE,
    FLARE_WARNING,
    SWARM_RADIUS,
)
from app.logic.world.flares import RICHEST, FlareClock, plan_ejecta

SUN_RADIUS = 600.


def test_the_sun_warns_blazes_ejects_then_calms_down() -> None:
    clock = FlareClock(Random(1))
    assert clock.phase == 'quiet'
    assert FLARE_EVERY[0] <= clock.left <= FLARE_EVERY[1]
    changes = []
    for lasts in (clock.left, FLARE_WARNING, FLARE_BLAZE, EJECTA_STAYS):
        assert clock.update(lasts / 2) is None
        changes.append(clock.update(lasts / 2))
    assert changes == ['warns', 'blazes', 'ejects', 'falls']
    assert clock.phase == 'quiet'


def test_the_heat_surges_while_it_blazes() -> None:
    clock = FlareClock(Random(2))
    seen = [(clock.phase, clock.surge)]
    for lasts in (clock.left, FLARE_WARNING, FLARE_BLAZE / 2,
                  FLARE_BLAZE / 2):
        clock.update(lasts)
        seen.append((clock.phase, clock.surge))
    assert seen == [
        ('quiet', 1.), ('warning', 1.), ('blazing', pytest.approx(1.)),
        ('blazing', pytest.approx(FLARE_SURGE)), ('ejecta', 1.),
    ]


def test_ejecta_are_of_the_rarest_ore_close_to_the_sun() -> None:
    ejecta = plan_ejecta(Random(3), SUN_RADIUS)
    assert len(ejecta) == EJECTA_ASTEROIDS
    low, high = EJECTA_ORBIT
    for asteroid in ejecta:
        assert asteroid.mineral in RICHEST
        assert SUN_RADIUS + low <= asteroid.orbit_radius <= SUN_RADIUS + high
        assert asteroid.radius > SWARM_RADIUS[0]


def test_ejecta_are_thrown_together() -> None:
    angles = [a.orbit_angle for a in plan_ejecta(Random(4), SUN_RADIUS)]
    middle = math.atan2(sum(map(math.sin, angles)),
                        sum(map(math.cos, angles)))
    assert all(
        abs(math.remainder(angle - middle, 2 * math.pi)) < math.pi / 2
        for angle in angles
    )


def test_the_richest_ore_is_the_rarest() -> None:
    frequencies = sorted(mineral.frequency for mineral in MINERALS.values())
    assert all(MINERALS[name].frequency in frequencies[:4] for name in RICHEST)
