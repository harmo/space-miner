import pytest

from app.logic.mining.minerals import MINERALS
from app.logic.mining.ore import (
    Deposits,
    cargo_fill,
    cargo_lines,
    cargo_load,
    cargo_room,
    cargo_total,
    mineral_of,
    ore_in,
    withdraw,
)
from app.logic.ship.config import LASER_RATE
from app.logic.world.space import Celestial


def asteroid(entity_id: int = 0, radius: float = 8.) -> Celestial:
    return Celestial(entity_id, radius)


def test_bigger_asteroids_hold_more_ore() -> None:
    assert ore_in(10.) == pytest.approx(4 * ore_in(5.))


def test_untouched_asteroid_is_full() -> None:
    target = asteroid()
    deposits = Deposits()
    assert deposits.left(target) == ore_in(target.radius)
    assert deposits.progress(target) == 0.


def test_laser_extracts_at_its_rate() -> None:
    target = asteroid()
    deposits = Deposits()
    extracted = deposits.mine(target, .5, LASER_RATE)
    assert extracted == pytest.approx(LASER_RATE * .5)
    assert deposits.left(target) == pytest.approx(
        ore_in(target.radius) - LASER_RATE * .5
    )


def test_cannot_extract_more_than_what_is_left() -> None:
    target = asteroid(radius=4.)
    deposits = Deposits()
    total = sum(deposits.mine(target, 1., LASER_RATE) for _ in range(100))
    assert total == pytest.approx(ore_in(target.radius))
    assert deposits.left(target) == 0.
    assert deposits.progress(target) == pytest.approx(1.)


def test_asteroids_are_mined_separately() -> None:
    first, second = asteroid(1), asteroid(2)
    deposits = Deposits()
    deposits.mine(first, 1., LASER_RATE)
    assert deposits.left(second) == ore_in(second.radius)


def test_forgotten_asteroid_is_full_again() -> None:
    # Entity ids get reused for new asteroids
    target = asteroid()
    deposits = Deposits()
    deposits.mine(target, 1., LASER_RATE)
    deposits.forget(target)
    assert deposits.left(target) == ore_in(target.radius)


def test_asteroids_are_rock_unless_told() -> None:
    assert mineral_of(Celestial(0, 8.)).name == 'Roche'
    assert mineral_of(Celestial(0, 8., mineral='gold')).name == 'Or'


def test_empty_cargo_shows_nothing() -> None:
    assert cargo_lines({}, None) == []
    assert cargo_lines({'rock': .4}, None) == []


def test_cargo_shows_what_it_holds_in_order() -> None:
    lines = cargo_lines({'gold': 2.7, 'rock': 12.}, None)
    assert [(line.mineral, line.amount) for line in lines] == [
        ('rock', 12), ('gold', 2),
    ]
    assert lines[1].name == 'Or'
    assert lines[1].color == MINERALS['gold'].color


def test_mineral_being_mined_shows_before_its_first_unit() -> None:
    lines = cargo_lines({'rock': 12.}, 'gold')
    assert [(line.mineral, line.amount, line.mining) for line in lines] == [
        ('rock', 12, False), ('gold', 0, True),
    ]


def test_cargo_counts_float_sums_right() -> None:
    lines = cargo_lines({'rock': 13.4 + 6.6 - 1e-12}, None)
    assert lines[0].amount == 20


def test_cargo_total() -> None:
    assert cargo_total({}) == 0
    assert cargo_total({'rock': 12.6, 'gold': 2.7}) == 14


# Capacity

def test_cargo_load_and_room() -> None:
    ore = {'rock': 12.5, 'gold': 2.5}
    assert cargo_load(ore) == 15.
    assert cargo_room(ore, 60.) == 45.
    assert cargo_fill(ore, 60.) == .25


def test_full_cargo_has_no_room() -> None:
    assert cargo_room({'rock': 60.}, 60.) == 0.
    assert cargo_room({'rock': 60. - 1e-9}, 60.) == 0.   # float leftovers
    assert cargo_fill({'rock': 70.}, 60.) == 1.


def test_mining_stops_when_the_cargo_is_full() -> None:
    target = asteroid(radius=10.)
    deposits = Deposits()
    assert deposits.mine(target, 1., LASER_RATE, room=.5) == .5
    assert deposits.mine(target, 1., LASER_RATE, room=0.) == 0.
    assert deposits.left(target) == pytest.approx(ore_in(10.) - .5)


def test_withdraw_leaves_what_remains() -> None:
    hold = {'iron': 5.}
    withdraw(hold, 'iron', 2.)
    assert hold == {'iron': 3.}


def test_withdraw_forgets_what_rounding_left() -> None:
    hold = {'iron': 5., 'gold': 1.}
    withdraw(hold, 'iron', 5. - 1e-9)
    assert hold == {'gold': 1.}


def test_withdraw_of_what_is_not_held() -> None:
    hold: dict[str, float] = {}
    withdraw(hold, 'iron', 0.)
    assert hold == {}
