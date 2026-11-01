from app.logic.base.board import Contracts
from app.logic.base.outposts import Progress
from app.logic.preferences import (
    Preferences,
    dump_preferences,
    load_preferences,
)
from app.logic.save import Save
from app.logic.slots import SLOTS, SlotSummary, summary


def test_a_slot_tells_how_far_its_game_went() -> None:
    save = Save(
        seed=1, credits=1200, contracts=Contracts(validated=7),
        outposts={
            'ares': Progress(2, contracts=Contracts(validated=3)),
            'ceres': Progress(0, {'rock': 5}),
        },
    )
    assert summary(save) == SlotSummary(1200, 10, 1)


def test_the_slot_played_last_is_remembered() -> None:
    preferences = Preferences(slot=2)
    assert load_preferences(dump_preferences(preferences)).slot == 2


def test_a_slot_out_of_range_comes_back_in_range() -> None:
    assert load_preferences('{"slot": 9}').slot == SLOTS
    assert load_preferences('{"slot": 0}').slot == 1
    assert load_preferences('{"slot": "two"}').slot == 1
    assert load_preferences('{"slot": true}').slot == 1
