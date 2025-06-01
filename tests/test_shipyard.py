from itertools import product

import pytest

from app.logic.ship.hulls import HULLS
from app.logic.ship.parts import PARTS, effects
from app.logic.ship.shipyard import (
    Design,
    bounds,
    design_key,
    options,
    pieces,
    ship_size,
    ship_stats,
)

SCOUT = HULLS['scout']
LOADED = Design(parts={
    'nose': 'heavy_laser', 'rear': 'engine',
    'left': 'cargo_pod', 'right': 'fins',
})


def test_bare_hull_has_the_hull_stats() -> None:
    stats = ship_stats(Design())
    assert stats.max_speed == SCOUT.max_speed
    assert stats.capacity == SCOUT.capacity
    assert stats.laser == SCOUT.laser
    assert stats.size == SCOUT.size


def test_parts_add_up_to_the_hull_stats() -> None:
    stats = ship_stats(LOADED)
    assert stats.laser == SCOUT.laser + PARTS['heavy_laser'].laser
    assert stats.capacity == SCOUT.capacity + PARTS['cargo_pod'].capacity
    assert stats.turn_speed == SCOUT.turn_speed + PARTS['fins'].turn_speed
    assert stats.max_speed == (
        SCOUT.max_speed + PARTS['engine'].max_speed
        + PARTS['heavy_laser'].max_speed
    )


def test_parts_make_the_ship_bigger() -> None:
    length, width = ship_size(LOADED)
    assert length > SCOUT.size[0] + PARTS['engine'].size[0]
    assert width > SCOUT.size[1] + PARTS['cargo_pod'].size[1]


def test_ship_is_centered() -> None:
    for design in (Design(), LOADED, Design(parts={'nose': 'laser'})):
        left, bottom, length, width = bounds(
            [rect for _, rect in pieces(design)]
        )
        assert left == pytest.approx(-length / 2)
        assert bottom == pytest.approx(-width / 2)


def test_parts_stick_out_where_they_attach() -> None:
    drawn = dict(pieces(LOADED))
    hull_x, hull_y, hull_length, hull_width = drawn['hull_scout']
    laser_x, _, laser_length, _ = drawn['heavy_laser']
    assert hull_x < laser_x < hull_x + hull_length < laser_x + laser_length
    engine_x, _, _, _ = drawn['engine']
    assert engine_x < hull_x
    _, pod_y, _, pod_height = drawn['cargo_pod']
    assert pod_y < hull_y + hull_width < pod_y + pod_height
    # Flipped on the right side
    _, fins_y, _, _ = drawn['fins_mirrored']
    assert fins_y < hull_y


def test_hull_covers_the_parts() -> None:
    assert pieces(LOADED)[-1][0] == 'hull_scout'


def every_design() -> list[Design]:
    """ Internal slots aside, which only change how far scanners reach """
    slots = [
        slot_id for slot_id, slot in SCOUT.slots.items()
        if slot.kind != 'internal'
    ]
    choices = [options(Design(), slot) for slot in slots]
    return [
        Design(parts={
            slot: part for slot, part in zip(slots, parts, strict=True)
            if part is not None
        })
        for parts in product(*choices)
    ]


def test_every_design_can_fly_and_mine() -> None:
    for design in every_design():
        stats = ship_stats(design)
        assert stats.max_speed >= 100
        assert stats.thrust >= .5
        assert stats.turn_speed >= 2
        assert stats.capacity >= SCOUT.capacity
        assert stats.laser >= SCOUT.laser


def test_plenty_of_parts_for_each_kind_of_slot() -> None:
    kinds = [part.kind for part in PARTS.values()]
    assert all(kinds.count(kind) >= 8 for kind in ('nose', 'rear', 'side'))


def test_the_best_laser_mines_everything() -> None:
    best = max(ship_stats(design).laser for design in every_design())
    assert best >= 4


def test_effects_of_a_part() -> None:
    assert effects(PARTS['laser']) == '+1 laser'
    assert effects(PARTS['container']) == (
        '-50 vitesse · -1.5 maniabilité · +30 soute'
    )
    assert all(effects(part) for part in PARTS.values())


def test_slots_take_parts_of_their_kind() -> None:
    nose = options(Design(), 'nose')
    assert nose[0] is None
    assert all(part and PARTS[part].kind == 'nose' for part in nose[1:])
    assert 'quantum_laser' in nose
    assert options(Design(), 'left') == options(Design(), 'right')
    assert 'engine' not in options(Design(), 'left')


def test_same_parts_same_key() -> None:
    first = Design(parts={'nose': 'laser', 'rear': 'engine'})
    second = Design(parts={'rear': 'engine', 'nose': 'laser'})
    assert design_key(first) == design_key(second)
    assert design_key(first) != design_key(Design())


def test_scanners_reach_farther_and_do_not_show() -> None:
    assert ship_stats(Design()).scan == 0
    scanned = Design(parts={'internal': 'long_scanner'})
    assert ship_stats(scanned).scan == PARTS['long_scanner'].scan
    assert pieces(scanned) == pieces(Design())
    assert ship_size(scanned) == ship_size(Design())


def test_some_hulls_add_to_the_scanners() -> None:
    assert ship_stats(Design('driller')).scan == 0
    scanned = Design('driller', {'internal_1': 'scanner'})
    assert ship_stats(scanned).scan == (
        HULLS['driller'].scan + PARTS['scanner'].scan
    )
