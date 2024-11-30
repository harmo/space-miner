from app.logic.ship.lasers import LASERS, laser


def test_each_level_is_more_powerful_and_wider() -> None:
    powers = [beam.power for beam in LASERS]
    widths = [beam.width for beam in LASERS]
    assert powers == sorted(set(powers))
    assert widths == sorted(set(widths))
    assert len({beam.color for beam in LASERS}) == len(LASERS)


def test_levels_beyond_the_best_are_the_best() -> None:
    assert laser(1) == LASERS[0]
    assert laser(len(LASERS) + 2) == LASERS[-1]
    assert laser(0) == LASERS[0]
