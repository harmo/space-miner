import json

import pytest

from app.logic.base.missions import Mission
from app.logic.preferences import (
    Preferences,
    dump_preferences,
    load_preferences,
)
from app.logic.save import Save, SaveError, dump, load
from app.logic.ship.scanner import LOOKED_FOR
from app.logic.ship.shipyard import Design

MISSION = Mission('Fonderie Lunaire', {'iron': 12, 'gold': 3}, 640, 3)
SAVE = Save(
    seed=1234, credits=5600,
    design=Design(parts={'nose': 'laser', 'left': 'fins'}),
    hulls=['scout', 'hauler'],
    spares={'engine': 1, 'fins': 2},
    stock={'iron': 12.5, 'crystal': 3.},
    cargo={'gold': 4.25},
    validated=7, seen_tier=2,
    offers=[MISSION, Mission('Comptoir Orion', {'copper': 9}, 300)],
    active=[Mission('Institut Cassini', {'ruby': 2}, 900)],
    looked_for=['gold', 'ruby'],
    mission_level=3,
)


def test_a_saved_game_comes_back_as_it_was() -> None:
    assert load(dump(SAVE)) == SAVE


def test_a_new_game_saves_too() -> None:
    assert load(dump(Save(seed=1))) == Save(seed=1)


def test_unknown_parts_and_minerals_are_left_out() -> None:
    data = json.loads(dump(SAVE))
    data['design']['parts'] = {'nose': 'warp_drive', 'rear': 'engine',
                               'left': 'laser'}
    data['spares']['warp_drive'] = 1
    data['stock']['unobtainium'] = 5.
    data['active'].append(
        {'client': 'X', 'wanted': {'unobtainium': 2}, 'reward': 10}
    )
    save = load(json.dumps(data))
    # A laser doesn't go on a side either
    assert save.design == Design(parts={'rear': 'engine'})
    assert 'warp_drive' not in save.spares
    assert 'unobtainium' not in save.stock
    assert save.active == SAVE.active


@pytest.mark.parametrize('text', [
    '', 'not json', '[]', '{}', '{"version": 99}',
    dump(SAVE).replace('"credits": 5600', '"credits": "lots"'),
])
def test_what_is_not_a_saved_game_is_refused(text: str) -> None:
    with pytest.raises(SaveError):
        load(text)


def test_preferences() -> None:
    preferences = Preferences(orbits=False, fullscreen=False, sound=False)
    assert load_preferences(dump_preferences(preferences)) == preferences
    assert load_preferences('{"orbits": "no", "unknown": 1}') == (
        Preferences()
    )
    assert load_preferences('garbage') == Preferences()


def test_older_saves_own_the_first_hull_and_the_ship_s() -> None:
    data = json.loads(dump(SAVE))
    del data['hulls']
    data['design'] = {'hull': 'driller', 'parts': {}}
    assert load(json.dumps(data)).hulls == ['scout', 'driller']


def test_older_saves_look_for_what_is_worth_it() -> None:
    data = json.loads(dump(SAVE))
    del data['looked_for']
    assert load(json.dumps(data)).looked_for == LOOKED_FOR


def test_older_saves_have_missions_of_the_first_level() -> None:
    data = json.loads(dump(SAVE))
    del data['mission_level']
    for mission in data['offers']:
        del mission['level']
    save = load(json.dumps(data))
    assert save.mission_level == 1
    assert all(mission.level == 1 for mission in save.offers)
