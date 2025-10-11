""" Draw the hulls and the parts of the ships, into assets/images/ships/.
Parts of the side slots are drawn for the left side and flipped for the
right one.

    uv run python -m tools.draw_ship
"""

from pathlib import Path

from PIL import Image

from app.logic.ship.hulls import HULLS
from app.logic.ship.parts import PARTS

from . import draw_hulls as hulls
from . import draw_nose as nose
from . import draw_rear as rear
from . import draw_sides as sides
from .sketch import (
    PORT,
    STARBOARD,
    Drawing,
    Sketch,
)

SHIPS_DIR = Path(__file__).parent.parent / 'assets' / 'images' / 'ships'

DRAWINGS: dict[str, Drawing] = {
    'hull_scout': hulls.draw_scout,
    'hull_hauler': hulls.draw_hauler,
    'hull_driller': hulls.draw_driller,
    'hull_cruiser': hulls.draw_cruiser,
    'laser': nose.draw_laser,
    'heavy_laser': nose.draw_heavy_laser,
    'pulse_laser': nose.draw_pulse_laser,
    'quantum_laser': nose.draw_quantum_laser,
    'stellar_laser': nose.draw_stellar_laser,
    'nose_cone': nose.draw_nose_cone,
    'front_hold': nose.draw_front_hold,
    'collector': nose.draw_collector,
    'engine': rear.draw_engine,
    'ion_engine': rear.draw_ion_engine,
    'twin_engine': rear.draw_twin_engine,
    'vector_nozzle': rear.draw_vector_nozzle,
    'rear_hold': rear.draw_rear_hold,
    'afterburner': rear.draw_afterburner,
    'solar_sail': rear.draw_solar_sail,
    'fusion_engine': rear.draw_fusion_engine,
    'cargo_pod': sides.draw_cargo_pod,
    'container': sides.draw_container,
    'fins': sides.fins_drawing(PORT),
    'delta_wing': sides.delta_wing_drawing(PORT),
    'side_thruster': sides.draw_side_thruster,
    'ion_pod': sides.draw_ion_pod,
    'cargo_bay': sides.draw_cargo_bay,
    'gyro': sides.draw_gyro,
    'wing_pod': sides.wing_pod_drawing(PORT),
}
# Side parts look different on the right side, before being flipped
RIGHT_DRAWINGS: dict[str, Drawing] = {
    'fins': sides.fins_drawing(STARBOARD),
    'delta_wing': sides.delta_wing_drawing(STARBOARD),
    'wing_pod': sides.wing_pod_drawing(STARBOARD),
}


def draw(size: tuple[float, float], drawing: Drawing) -> Image.Image:
    sketch = Sketch(size)
    drawing(sketch)
    return sketch.result()


def save(image: Image.Image, name: str) -> None:
    image.save(SHIPS_DIR / f'{name}.png')
    print(f'ships/{name}.png')


def main() -> None:
    SHIPS_DIR.mkdir(exist_ok=True)
    for hull_id, hull in HULLS.items():
        name = f'hull_{hull_id}'
        save(draw(hull.size, DRAWINGS[name]), name)
    for part_id, part in PARTS.items():
        if part.kind == 'internal':
            continue                    # not drawn on the ship
        save(draw(part.size, DRAWINGS[part_id]), part_id)
        if part.kind == 'side':
            drawing = RIGHT_DRAWINGS.get(part_id, DRAWINGS[part_id])
            right = draw(part.size, drawing)
            save(
                right.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
                f'{part_id}_mirrored',
            )


if __name__ == '__main__':
    main()
