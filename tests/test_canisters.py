import math
from random import Random

import pytest

from app.logic.mining.canisters import (
    drift,
    eject_cargo,
    flow_velocity,
    settle,
)
from app.logic.mining.config import (
    CANISTER_DRAG,
    CANISTER_ORBIT_ALTITUDE,
    CANISTER_ORBIT_PACE,
    CANISTER_SPEED,
    CANISTER_SPIN,
    CANISTER_SPREAD,
    CANISTER_UNITS,
)
from app.logic.world.space import Celestial, Orbit, Vec2, angle_diff

ORE = {'rock': 23., 'gold': 6., 'ice': 1e-9}


def test_cargo_is_split_in_canisters() -> None:
    plans = eject_cargo(Random(0), ORE, (0., 0.), (0., 0.), 0.)
    minerals = [plan.mineral for plan in plans]
    assert minerals.count('rock') == math.ceil(23 / CANISTER_UNITS)
    assert minerals.count('gold') == 1
    assert 'ice' not in minerals                 # float leftover
    assert all(plan.amount <= CANISTER_UNITS for plan in plans)


def test_no_ore_is_lost_in_the_split() -> None:
    plans = eject_cargo(Random(0), ORE, (0., 0.), (0., 0.), 0.)
    for mineral in ('rock', 'gold'):
        total = sum(p.amount for p in plans if p.mineral == mineral)
        assert total == pytest.approx(ORE[mineral])


def test_empty_cargo_throws_nothing() -> None:
    assert eject_cargo(Random(0), {}, (0., 0.), (0., 0.), 0.) == []


def test_canisters_fly_away_from_what_was_hit() -> None:
    away = math.radians(120)
    velocity = (30., -10.)
    plans = eject_cargo(
        Random(1), {'rock': 60.}, (5., 7.), velocity, away
    )
    for plan in plans:
        assert plan.pos == (5., 7.)
        dx, dy = plan.velocity[0] - velocity[0], plan.velocity[1] - velocity[1]
        speed = math.hypot(dx, dy)
        assert CANISTER_SPEED[0] <= speed <= CANISTER_SPEED[1]
        spread = math.degrees(abs(angle_diff(math.atan2(dy, dx), away)))
        assert spread <= CANISTER_SPREAD + 1e-9
        assert abs(plan.spin) <= math.radians(CANISTER_SPIN)


# Following the asteroids around

def test_flow_keeps_canisters_on_their_circle() -> None:
    center, pos = (100., 50.), (600., 50.)
    angular_speed, dt = .05, 1 / 60
    for _ in range(round(600 / dt)):            # 10 minutes
        vx, vy = flow_velocity(pos, center, (0., 0.), angular_speed, dt)
        pos = (pos[0] + vx * dt, pos[1] + vy * dt)
    assert math.dist(pos, center) == pytest.approx(500., rel=1e-6)
    angle = math.atan2(pos[1] - center[1], pos[0] - center[0])
    assert abs(angle_diff(angle, angular_speed * 600)) < 1e-6


def test_flow_moves_along_with_its_center() -> None:
    vx, vy = flow_velocity((10., 0.), (0., 0.), (25., -5.), 0., 1 / 60)
    assert (vx, vy) == pytest.approx((25., -5.))


def test_drift_fades_towards_the_flow() -> None:
    flow, velocity = (20., 0.), (120., 0.)
    speeds = []
    for _ in range(600):
        velocity = drift(velocity, flow, 1 / 60)
        speeds.append(velocity[0] - flow[0])
    assert speeds == sorted(speeds, reverse=True)
    # After one second, 60 frames
    assert speeds[59] == pytest.approx(100. * math.exp(-CANISTER_DRAG))
    assert speeds[-1] < 1.


# Settling on an orbit around a planet

DT = 1 / 60
ALTITUDE = 150.


def planet() -> Celestial:
    return Celestial(1, 200., pos=(1000., 500.), gravity=250.)


def settled(body: Celestial, pos: Vec2, velocity: Vec2,
            seconds: float) -> tuple[Vec2, Vec2]:
    """ Where a canister thrown from pos ends up, and how fast """
    for _ in range(round(seconds / DT)):
        velocity = settle(pos, velocity, body, ALTITUDE, DT)
        pos = (pos[0] + velocity[0] * DT, pos[1] + velocity[1] * DT)
    return pos, velocity


def test_canisters_settle_on_a_slow_orbit() -> None:
    body = planet()
    pos, velocity = settled(body, (1500., 500.), (0., 0.), 60.)
    distance = math.dist(pos, body.pos)
    pull = math.hypot(*body.pull(*pos))
    assert math.hypot(*velocity) == pytest.approx(
        CANISTER_ORBIT_PACE * math.sqrt(pull * distance), rel=1e-2,
    )
    radial = (pos[0] - 1000.) * velocity[0] + (pos[1] - 500.) * velocity[1]
    assert abs(radial) / distance < 1.


def test_canisters_settle_progressively() -> None:
    body = planet()
    _, early = settled(body, (1500., 500.), (0., 0.), .5)
    orbit = math.sqrt(math.hypot(*body.pull(1500., 500.)) * 500.)
    assert 0. < math.hypot(*early) < orbit / 3


def test_canisters_all_orbit_the_same_way() -> None:
    body = planet()
    for thrown in (60., -60.):
        pos, velocity = settled(body, (1500., 500.), (0., thrown), 30.)
        dx, dy = pos[0] - 1000., pos[1] - 500.
        assert dx * velocity[1] - dy * velocity[0] > 0


@pytest.mark.parametrize('distance, thrown', [
    (210., (-50., 0.)), (500., (0., 0.)), (1100., (80., 40.)),
])
def test_canisters_gather_at_their_height(distance: float,
                                          thrown: Vec2) -> None:
    body = planet()
    pos, _ = settled(body, (1000. + distance, 500.), thrown, 40.)
    assert math.dist(pos, body.pos) - body.radius == pytest.approx(
        ALTITUDE, abs=8.,
    )


def test_canisters_are_thrown_for_orbits_of_their_own() -> None:
    plans = eject_cargo(Random(4), {'rock': 100.}, (0., 0.), (0., 0.), 0.)
    low, high = CANISTER_ORBIT_ALTITUDE
    assert all(low <= plan.altitude <= high for plan in plans)
    assert len({plan.altitude for plan in plans}) == len(plans)


def test_orbits_hold_for_as_long_as_a_game() -> None:
    body = planet()
    pos, velocity = settled(body, (1500., 500.), (0., 0.), 40.)
    distance = math.dist(pos, body.pos)
    pos, _ = settled(body, pos, velocity, 600.)
    assert math.dist(pos, body.pos) == pytest.approx(distance, rel=.01)


def test_canisters_keep_up_with_a_moving_planet() -> None:
    sun = Celestial(0, 600.)
    body = Celestial(1, 200., orbit=Orbit(sun, 5000., 25., 0.), gravity=250.)
    pos = (body.pos[0] + 500., body.pos[1])
    velocity = body.velocity
    for _ in range(round(40 / DT)):
        velocity = settle(pos, velocity, body, ALTITUDE, DT)
        pos = (pos[0] + velocity[0] * DT, pos[1] + velocity[1] * DT)
        assert body.orbit is not None
        body.orbit.advance(DT)
    assert math.dist(pos, body.pos) == pytest.approx(
        body.radius + ALTITUDE, rel=.05,
    )
