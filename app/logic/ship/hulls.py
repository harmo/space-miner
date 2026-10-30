""" Catalog of the hulls ships are built on, and of their slots. Bigger
hulls come in higher tiers, with more slots for parts. Sizes are in
pixels of the world, from the center of the hull, its nose along +x. """

from dataclasses import dataclass
from typing import Literal

from ..world.space import Vec2

# Internal slots hold what doesn't show, like scanners
SlotKind = Literal['nose', 'rear', 'side', 'internal']


@dataclass(frozen=True)
class Slot:
    name: str                 # shown in the hangar
    kind: SlotKind
    anchor: Vec2              # where parts attach, from the hull center
    mirrored: bool = False    # parts on the right side are drawn flipped


@dataclass(frozen=True)
class Hull:
    name: str
    size: Vec2
    slots: dict[str, Slot]
    max_speed: float
    thrust: float             # how fast velocity converges while thrusting
    turn_speed: float         # how fast the ship faces the pointer
    capacity: float           # units of ore, of any mineral
    laser: int                # level of the laser built in
    # Reach added to the scanners fitted, none without any
    scan: float
    tank: float               # units of fuel
    price: int = 0            # credits
    # Ore taken from the depot to build it, by mineral
    materials: tuple[tuple[str, int], ...] = ()
    tier: int = 1             # sold once the reputation reaches it


def internals(count: int) -> dict[str, Slot]:
    """ Slots inside the hull """
    if count == 1:
        return {'internal': Slot('Interne', 'internal', (0., 0.))}
    return {
        f'internal_{index}': Slot(f'Interne {index}', 'internal', (0., 0.))
        for index in range(1, count + 1)
    }


# Pairs of side slots on hulls with several of them
WHERE = {'': '', 'front': ' avant', 'back': ' arrière'}


def sides(x: float, y: float, where: str = '') -> dict[str, Slot]:
    """ A pair of side slots, `x` along the ship, `y` off its middle """
    suffix = f'_{where}' if where else ''
    return {
        f'left{suffix}': Slot(f'Gauche{WHERE[where]}', 'side', (x, y)),
        f'right{suffix}': Slot(
            f'Droite{WHERE[where]}', 'side', (x, -y), mirrored=True,
        ),
    }


HULLS = {
    'scout': Hull(
        'Éclaireur', (26., 16.),
        {
            'nose': Slot('Avant', 'nose', (13., 0.)),
            'rear': Slot('Arrière', 'rear', (-13., 0.)),
            'left': Slot('Côté gauche', 'side', (-3., 7.)),
            'right': Slot(
                'Côté droit', 'side', (-3., -7.), mirrored=True,
            ),
            **internals(1),
        },
        max_speed=350., thrust=1.2, turn_speed=6., capacity=30., laser=1,
        scan=0., tank=100.,
    ),
    # Slow and roomy, four sides for cargo
    'hauler': Hull(
        'Cargo', (40., 22.),
        {
            'nose': Slot('Avant', 'nose', (20., 0.)),
            'rear': Slot('Arrière', 'rear', (-20., 0.)),
            **sides(9., 10., 'front'),
            **sides(-10., 10., 'back'),
            **internals(2),
        },
        max_speed=280., thrust=1., turn_speed=4.5, capacity=60., laser=1,
        scan=0., tank=160.,
        price=8000, materials=(('iron', 20),), tier=2,
    ),
    # A strong laser built in, which mines much faster
    'driller': Hull(
        'Foreuse', (32., 18.),
        {
            'nose': Slot('Avant', 'nose', (16., 0.)),
            'rear': Slot('Arrière', 'rear', (-16., 0.)),
            **sides(-4., 8.),
            **internals(2),
        },
        max_speed=330., thrust=1.3, turn_speed=5.5, capacity=40., laser=2,
        scan=2000., tank=120.,
        price=20000, materials=(('copper', 15), ('crystal', 8)), tier=3,
    ),
    # Two of everything
    'cruiser': Hull(
        'Croiseur', (48., 26.),
        {
            'nose_left': Slot('Avant gauche', 'nose', (21., 5.)),
            'nose_right': Slot('Avant droit', 'nose', (21., -5.)),
            'rear_left': Slot('Arrière gauche', 'rear', (-23.5, 6.)),
            'rear_right': Slot('Arrière droit', 'rear', (-23.5, -6.)),
            **sides(10., 12., 'front'),
            **sides(-12., 12., 'back'),
            **internals(3),
        },
        max_speed=380., thrust=1.4, turn_speed=5., capacity=50., laser=1,
        scan=1000., tank=200.,
        price=50000, materials=(('stellarium', 8), ('antimatter', 4)),
        tier=5,
    ),
}
