from pathlib import Path

from app.logic.config import IMAGES
from app.logic.ship.config import MIN_SPEED
from app.logic.ship.hulls import HULLS
from app.logic.ship.lasers import BEST
from app.logic.ship.parts import PARTS
from app.logic.ship.shipyard import (
    Design,
    bounds,
    options,
    pieces,
    ship_stats,
    transfer,
)

FULL_SCOUT = Design(parts={
    'nose': 'laser', 'rear': 'engine', 'left': 'fins', 'right': 'cargo_pod',
})


def test_hulls_grow_with_their_tier() -> None:
    hulls = sorted(HULLS.values(), key=lambda hull: hull.tier)
    assert hulls[0] == HULLS['scout'] and hulls[0].price == 0
    prices = [hull.price for hull in hulls]
    assert prices == sorted(prices)
    outside = [slot for slot in HULLS['cruiser'].slots.values()
               if slot.kind != 'internal']
    assert len(outside) == 8
    internal = {
        hull_id: sum(slot.kind == 'internal' for slot in hull.slots.values())
        for hull_id, hull in HULLS.items()
    }
    assert internal == {'scout': 1, 'hauler': 2, 'driller': 2, 'cruiser': 3}
    assert HULLS['hauler'].capacity > HULLS['scout'].capacity
    assert HULLS['driller'].laser > HULLS['scout'].laser


def test_only_side_parts_are_drawn_flipped() -> None:
    for hull in HULLS.values():
        for slot_id, slot in hull.slots.items():
            assert slot.mirrored == (slot_id.startswith('right'))
            assert not slot.mirrored or slot.kind == 'side'


def test_every_part_fits_every_hull_and_is_drawn() -> None:
    for hull_id in HULLS:
        bare = Design(hull_id)
        for slot_id in HULLS[hull_id].slots:
            for part_id in options(bare, slot_id)[1:]:
                assert part_id is not None
                design = Design(hull_id, {slot_id: part_id})
                left, bottom, length, width = bounds(
                    [rect for _, rect in pieces(design)]
                )
                assert left == -length / 2 and bottom == -width / 2
                for image, _ in pieces(design):
                    assert Path(f'{IMAGES}/ships/{image}.png').is_file()


def test_parts_move_onto_the_slots_of_their_kind() -> None:
    hauler, left = transfer(FULL_SCOUT, 'hauler')
    assert left == []
    assert hauler.hull == 'hauler'
    assert sorted(hauler.parts.values()) == sorted(FULL_SCOUT.parts.values())
    assert hauler.parts['nose'] == 'laser'
    assert hauler.parts['rear'] == 'engine'


def test_parts_finding_no_slot_are_left() -> None:
    cruiser = Design('cruiser', {
        'nose_left': 'laser', 'nose_right': 'collector',
        'left_front': 'fins', 'left_back': 'gyro',
    })
    scout, left = transfer(cruiser, 'scout')
    assert scout.parts == {'nose': 'laser', 'left': 'fins', 'right': 'gyro'}
    assert left == ['collector']


def test_heavy_ships_still_fly() -> None:
    heaviest = Design('cruiser', {
        'nose_left': 'quantum_laser', 'nose_right': 'quantum_laser',
        'rear_left': 'rear_hold', 'rear_right': 'rear_hold',
        'left_front': 'container', 'left_back': 'container',
        'right_front': 'container', 'right_back': 'container',
    })
    stats = ship_stats(heaviest)
    assert stats.max_speed == MIN_SPEED
    assert stats.thrust > 0 and stats.turn_speed > 0
    assert stats.laser == BEST


def test_the_driller_mines_better_from_the_start() -> None:
    assert ship_stats(Design('driller')).laser == 2
    assert ship_stats(Design('driller', {'nose': 'stellar_laser'})).laser == (
        BEST
    )
    assert PARTS['stellar_laser'].laser + HULLS['driller'].laser == BEST
