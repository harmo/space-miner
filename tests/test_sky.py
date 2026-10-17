import pytest

from app.logic.sky import tile_coords

SIZE = (800., 600.)
TILE = 1000.


def test_the_screen_on_the_tile() -> None:
    left, bottom, right, _, _, top, _, _ = tile_coords(
        (0., 0.), .1, SIZE, TILE
    )
    assert right - left == pytest.approx(.8)
    assert top - bottom == pytest.approx(.6)


def test_slides_slower_than_the_ship() -> None:
    still = tile_coords((0., 0.), .1, SIZE, TILE)
    moved = tile_coords((2000., 500.), .1, SIZE, TILE)
    assert moved[0] - still[0] == pytest.approx(.2)
    assert moved[1] - still[1] == pytest.approx(.05)


def test_stays_on_the_first_tile() -> None:
    """ The image repeats: far travels come back near the first copy """
    coords = tile_coords((1e9, -1e9), .1, SIZE, TILE)
    assert 0 <= coords[0] < 1 and 0 <= coords[1] < 1


def test_on_whole_pixels() -> None:
    """ Not to make the smallest stars flicker """
    for travel in (0., 3.3, 7.77, 1234.5678):
        coords = tile_coords((travel, travel), .1, SIZE, TILE)
        assert coords[0] * TILE == pytest.approx(round(coords[0] * TILE))
        assert coords[1] * TILE == pytest.approx(round(coords[1] * TILE))
