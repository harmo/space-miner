""" Catalog of the parts fitting the slots of the hulls. Each part improves
the ship, most at the cost of something else. Better parts come in higher
tiers, sold once the reputation of the player is high enough, for more
credits and rarer ore. """

from dataclasses import dataclass

from ..world.space import Vec2
from .hulls import SlotKind


@dataclass(frozen=True)
class Part:
    name: str
    kind: SlotKind
    size: Vec2                # along the ship, across it
    max_speed: float = 0.
    thrust: float = 0.
    turn_speed: float = 0.
    capacity: float = 0.
    laser: int = 0
    scan: float = 0.          # reach of scanners, added to the hull's
    price: int = 0            # credits
    # Ore taken from the depot to build it, by mineral
    materials: tuple[tuple[str, int], ...] = ()
    tier: int = 1             # sold once the reputation reaches it


# By slot kind, then by tier, in the order the hangar lists them
PARTS = {
    # Nose
    'laser': Part(
        'Laser renforcé', 'nose', (12., 6.), laser=1, price=500,
    ),
    'nose_cone': Part(
        'Carénage', 'nose', (9., 12.), max_speed=60., turn_speed=1.,
        price=600,
    ),
    'front_hold': Part(
        'Soute frontale', 'nose', (12., 10.), capacity=10., max_speed=-20.,
        price=500,
    ),
    'heavy_laser': Part(
        'Laser lourd', 'nose', (16., 9.), laser=2, max_speed=-40.,
        price=1500, materials=(('copper', 10),), tier=2,
    ),
    'pulse_laser': Part(
        'Laser à impulsions', 'nose', (14., 8.), laser=2, turn_speed=1.,
        price=3000, materials=(('copper', 12), ('crystal', 4)), tier=3,
    ),
    'quantum_laser': Part(
        'Laser quantique', 'nose', (20., 11.),
        laser=3, max_speed=-80., thrust=-.2,
        price=6000, materials=(('crystal', 10), ('nebulite', 4)), tier=4,
    ),
    'collector': Part(
        'Collecteur', 'nose', (12., 12.), capacity=15., max_speed=20.,
        price=4700, materials=(('ruby', 3),), tier=4,
    ),
    'stellar_laser': Part(
        'Laser stellaire', 'nose', (22., 12.), laser=3, max_speed=-20.,
        price=12700, materials=(('stellarium', 6), ('antimatter', 2)),
        tier=5,
    ),
    # Rear
    'engine': Part(
        'Réacteur', 'rear', (10., 12.), max_speed=150., thrust=.3,
        price=700,
    ),
    'rear_hold': Part(
        'Soute arrière', 'rear', (12., 12.), capacity=20., max_speed=-30.,
        price=1000, tier=2,
    ),
    'vector_nozzle': Part(
        'Tuyère orientable', 'rear', (8., 10.), thrust=.2, turn_speed=4.,
        price=1200, tier=2,
    ),
    'afterburner': Part(
        'Postcombustion', 'rear', (12., 11.),
        max_speed=100., thrust=.8, turn_speed=-1.,
        price=1700, materials=(('iron', 15),), tier=2,
    ),
    'ion_engine': Part(
        'Propulseur ionique', 'rear', (14., 10.), max_speed=250., thrust=-.2,
        price=3200, materials=(('helium3', 6),), tier=3,
    ),
    'twin_engine': Part(
        'Double réacteur', 'rear', (12., 15.),
        max_speed=200., thrust=.6, turn_speed=-1.,
        price=3700, materials=(('iron', 15), ('uranium', 5)), tier=3,
    ),
    'solar_sail': Part(
        'Voile solaire', 'rear', (10., 18.), max_speed=120., turn_speed=2.,
        price=5300, materials=(('stellarium', 3),), tier=4,
    ),
    'fusion_engine': Part(
        'Réacteur à fusion', 'rear', (14., 14.), max_speed=320., thrust=.6,
        price=11700, materials=(('uranium', 10), ('antimatter', 3)),
        tier=5,
    ),
    # Sides
    'fins': Part(
        'Stabilisateur', 'side', (14., 8.), turn_speed=3., price=400,
    ),
    'cargo_pod': Part(
        'Module de soute', 'side', (18., 8.), capacity=15., price=500,
    ),
    'delta_wing': Part(
        'Aile delta', 'side', (18., 9.), turn_speed=2., max_speed=40.,
        price=1300, tier=2,
    ),
    'side_thruster': Part(
        'Propulseur latéral', 'side', (12., 8.), thrust=.3, turn_speed=2.,
        price=1500, tier=2,
    ),
    'container': Part(
        'Grand conteneur', 'side', (24., 10.),
        capacity=30., max_speed=-50., turn_speed=-1.5,
        price=2500, materials=(('iron', 20),), tier=3,
    ),
    'ion_pod': Part(
        'Nacelle ionique', 'side', (14., 8.), max_speed=80., thrust=.4,
        price=2700, materials=(('helium3', 4),), tier=3,
    ),
    'cargo_bay': Part(
        'Soute renforcée', 'side', (20., 10.), capacity=25.,
        price=5000, materials=(('iron', 30), ('ruby', 2)), tier=4,
    ),
    'gyro': Part(
        'Gyrostabilisateur', 'side', (10., 7.), turn_speed=5., thrust=.2,
        price=5000, materials=(('uranium', 6),), tier=4,
    ),
    'wing_pod': Part(
        'Aile-soute', 'side', (22., 10.),
        capacity=15., turn_speed=2., max_speed=30.,
        price=10000, materials=(('nebulite', 6), ('stellarium', 3)),
        tier=5,
    ),
    # Internal, not drawn
    'scanner': Part(
        'Scanner', 'internal', (0., 0.), scan=3000., price=400,
    ),
    'long_scanner': Part(
        'Scanner longue portée', 'internal', (0., 0.), scan=6000.,
        price=1300, materials=(('copper', 6),), tier=2,
    ),
    'deep_scanner': Part(
        'Scanner profond', 'internal', (0., 0.), scan=10000.,
        price=3000, materials=(('crystal', 5),), tier=3,
    ),
    'quantum_scanner': Part(
        'Scanner quantique', 'internal', (0., 0.), scan=16000.,
        price=5300, materials=(('nebulite', 4),), tier=4,
    ),
}


def effects(part: Part) -> str:
    """ What the part changes, as shown in the hangar """
    changes = [
        (part.laser, 'laser', '{:+.0f}'),
        (part.max_speed, 'vitesse', '{:+.0f}'),
        (part.thrust, 'poussée', '{:+.1f}'),
        (part.turn_speed, 'maniabilité', '{:+g}'),
        (part.capacity, 'soute', '{:+.0f}'),
        (part.scan, 'portée de scan', '{:+.0f}'),
    ]
    return ' · '.join(
        f'{number.format(value)} {name}'
        for value, name, number in changes if value
    )
