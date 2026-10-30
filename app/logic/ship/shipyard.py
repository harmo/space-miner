""" Ships built from a hull, and parts grafted on its slots. Sizes are in
pixels of the world, ships face +x: their nose points right. """

from dataclasses import dataclass, field, replace

from ..world.space import Vec2
from .config import HULL_BURN, MIN_SPEED, MIN_THRUST, MIN_TURN_SPEED
from .hulls import HULLS, Hull, Slot
from .lasers import BEST
from .parts import PARTS, Part

# Lower left corner, width and height
Rect = tuple[float, float, float, float]

OVERLAP = 2.                  # parts sink this far into the hull
SHIP_PIXELS = 4               # of the images, per pixel of the world


@dataclass(frozen=True)
class Design:
    hull: str = 'scout'
    parts: dict[str, str] = field(default_factory=dict)   # slot: part


@dataclass(frozen=True)
class ShipStats:
    max_speed: float
    thrust: float
    turn_speed: float
    capacity: float
    laser: int
    scan: float               # reach of the scanners
    size: Vec2                # length, width
    tank: float = 0.          # units of fuel
    burn: float = 0.          # fuel a second at full thrust


def part_rect(slot: Slot, part: Part) -> Rect:
    """ Where the part lies, sticking out of the hull at its slot """
    length, width = part.size
    x, y = slot.anchor
    if slot.kind == 'nose':
        return x - OVERLAP, y - width / 2, length, width
    if slot.kind == 'rear':
        return x + OVERLAP - length, y - width / 2, length, width
    if slot.mirrored:
        return x - length / 2, y + OVERLAP - width, length, width
    return x - length / 2, y - OVERLAP, length, width


def hull_rect(hull: Hull) -> Rect:
    length, width = hull.size
    return -length / 2, -width / 2, length, width


def bounds(rects: list[Rect]) -> Rect:
    left = min(x for x, _, _, _ in rects)
    bottom = min(y for _, y, _, _ in rects)
    right = max(x + w for x, _, w, _ in rects)
    top = max(y + h for _, y, _, h in rects)
    return left, bottom, right - left, top - bottom


def on_hull(design: Design) -> list[tuple[str, Rect]]:
    """ Images of the ship and where they go, from the center of the hull.
    Parts first: the hull covers where they attach. Internal ones don't
    show. """
    hull = HULLS[design.hull]
    drawn = []
    for slot_id, part_id in design.parts.items():
        slot = hull.slots[slot_id]
        if slot.kind == 'internal':
            continue
        image = f'{part_id}_mirrored' if slot.mirrored else part_id
        drawn.append((image, part_rect(slot, PARTS[part_id])))
    drawn.append((f'hull_{design.hull}', hull_rect(hull)))
    return drawn


def center_of(design: Design) -> Vec2:
    """ Of the whole ship, which turns around it, from that of the hull """
    left, bottom, length, width = bounds(
        [rect for _, rect in on_hull(design)]
    )
    return left + length / 2, bottom + width / 2


def pieces(design: Design) -> list[tuple[str, Rect]]:
    """ Images of the ship and where they go, from its center """
    dx, dy = center_of(design)
    return [
        (image, (x - dx, y - dy, w, h))
        for image, (x, y, w, h) in on_hull(design)
    ]


def ship_size(design: Design) -> Vec2:
    """ Length and width of the whole ship """
    _, _, length, width = bounds([rect for _, rect in pieces(design)])
    return length, width


def scan_reach(hull: float, parts: list[float]) -> float:
    """ None without a scanner, the hull only adding to them """
    scanners = sum(parts)
    return hull + scanners if scanners > 0 else 0.


def ship_stats(design: Design) -> ShipStats:
    """ Those of the hull, changed by the parts, within bounds """
    hull = HULLS[design.hull]
    parts = [PARTS[part] for part in design.parts.values()]
    speed = hull.max_speed + sum(p.max_speed for p in parts)
    thrust = hull.thrust + sum(p.thrust for p in parts)
    turn_speed = hull.turn_speed + sum(p.turn_speed for p in parts)
    return ShipStats(
        max_speed=max(MIN_SPEED, speed),
        thrust=max(MIN_THRUST, thrust),
        turn_speed=max(MIN_TURN_SPEED, turn_speed),
        capacity=hull.capacity + sum(p.capacity for p in parts),
        laser=min(BEST, hull.laser + sum(p.laser for p in parts)),
        scan=scan_reach(hull.scan, [p.scan for p in parts]),
        size=ship_size(design),
        tank=hull.tank + sum(p.tank for p in parts),
        burn=max(0., HULL_BURN + sum(p.burn for p in parts)),
    )


def transfer(design: Design, hull_id: str) -> tuple[Design, list[str]]:
    """ The parts of the design on a new hull, each on the first free slot
    of its kind. Returns those finding none. """
    free = list(HULLS[hull_id].slots.items())
    parts: dict[str, str] = {}
    left: list[str] = []
    for part_id in design.parts.values():
        kind = PARTS[part_id].kind
        spot = next(
            (slot_id for slot_id, slot in free if slot.kind == kind), None
        )
        if spot is None:
            left.append(part_id)
        else:
            parts[spot] = part_id
            free = [(slot_id, slot) for slot_id, slot in free
                    if slot_id != spot]
    return Design(hull_id, parts), left


def options(design: Design, slot_id: str) -> list[str | None]:
    """ Parts fitting a slot, nothing first """
    kind = HULLS[design.hull].slots[slot_id].kind
    return [None, *(name for name, p in PARTS.items() if p.kind == kind)]


def fitted(design: Design, slot_id: str, part_id: str | None) -> Design:
    parts = {s: p for s, p in design.parts.items() if s != slot_id}
    if part_id is not None:
        parts[slot_id] = part_id
    return replace(design, parts=parts)


def design_key(design: Design) -> str:
    """ Same for designs looking the same """
    slots = ','.join(f'{s}={p}' for s, p in sorted(design.parts.items()))
    return f'{design.hull}:{slots}'
