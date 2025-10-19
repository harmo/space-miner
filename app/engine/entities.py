""" Creation and moves of KivEnt entities """

from collections.abc import Callable
from typing import Any

from cymunk import Body
from kivent_core.systems.renderers import Renderer

from ..logic.config import (
    COLLISION_CANISTER,
    COLLISION_ORBITER,
    COLLISION_PLANET,
    COLLISION_SHIP,
    PHYSICS_COMPONENT_ORDER,
    SYSTEMS,
)
from ..logic.mining.canisters import CanisterPlan, canister_texture
from ..logic.mining.config import CANISTER_SIZE
from ..logic.mining.minerals import display_scale
from ..logic.ship.config import SHIP_MASS
from ..logic.world.space import Vec2
from .textures import texture_size

GameWorld = Any               # KivEnt ships no type information
# Called by the physics engine with (space, arbiter), returns whether the
# collision happens
CollisionHandler = Callable[[Any, Any], bool]


def setup_state(gameworld: GameWorld) -> None:
    """ The only state of the game, where everything is drawn """
    gameworld.add_state(
        state_name='main',
        systems_added=['stars_renderer', 'rotate_renderer'],
        systems_removed=[], systems_paused=[],
        systems_unpaused=['stars_renderer', 'rotate_renderer'],
        screenmanager_screen='main'
    )


def setup_collisions(gameworld: GameWorld,
                     on_ship_contact: CollisionHandler) -> None:
    """ Only the ship collides: with the planets, the orbiters and the
    canisters. Everything else goes through each other. """
    def ignore(space: Any, arbiter: Any) -> bool:
        return False

    physics = gameworld.system_manager['cymunk_physics']
    for other in (COLLISION_ORBITER, COLLISION_PLANET):
        physics.add_collision_handler(
            COLLISION_ORBITER, other, begin_func=ignore
        )
        physics.add_collision_handler(
            COLLISION_SHIP, other, begin_func=on_ship_contact
        )
    physics.add_collision_handler(
        COLLISION_SHIP, COLLISION_CANISTER, begin_func=on_ship_contact
    )
    for other in (COLLISION_PLANET, COLLISION_ORBITER, COLLISION_CANISTER):
        physics.add_collision_handler(
            COLLISION_CANISTER, other, begin_func=ignore
        )


def create_round_entity(gameworld: GameWorld, texture: str, pos: Vec2,
                        radius: float, mass: float, collision_type: int,
                        angle: float = 0., velocity: Vec2 = (0., 0.),
                        angular_velocity: float = 0.,
                        display_radius: float | None = None) -> int:
    """ Round physics body drawn with `texture`. A mass of 0 makes a static
    body. """
    tex_width, tex_height = texture_size(texture)
    display_radius = display_radius or radius
    entity_id: int = gameworld.init_entity(
        components_to_use={
            'cymunk_physics': {
                'main_shape': 'circle',
                'position': pos,
                'angle': angle,
                'angular_velocity': angular_velocity,
                'velocity': velocity,
                'mass': mass,
                'col_shapes': [{
                    'shape_type': 'circle',
                    'elasticity': .5,
                    'collision_type': collision_type,
                    'friction': 1.,
                    'shape_info': {
                        'inner_radius': 0,
                        'outer_radius': radius,
                        'mass': mass,
                        'offset': (0, 0),
                    },
                }],
            },
            'position': pos,
            'rotate': 0,
            'rotate_renderer': {
                'texture': texture,
                'size': (
                    2 * display_radius,
                    2 * display_radius * tex_height / tex_width,
                ),
                'render': True,
            },
        },
        component_order=PHYSICS_COMPONENT_ORDER,
    )
    return entity_id


def create_ship_entity(gameworld: GameWorld, pos: Vec2, velocity: Vec2,
                       angle: float, texture: str, size: Vec2) -> int:
    length, width = size
    entity_id: int = gameworld.init_entity(
        components_to_use={
            'cymunk_physics': {
                'main_shape': 'box',
                'position': pos,
                'angle': angle,
                'angular_velocity': 0,
                'velocity': velocity,
                'mass': SHIP_MASS,
                'col_shapes': [{
                    'shape_type': 'box',
                    'elasticity': .5,
                    'collision_type': COLLISION_SHIP,
                    'friction': 1.,
                    'shape_info': {
                        'width': length,
                        'height': width,
                        'mass': SHIP_MASS,
                    },
                }],
            },
            'position': pos,
            'rotate': 0,
            'rotate_renderer': {
                'texture': texture,
                'size': size,
                'render': True,
            },
        },
        component_order=PHYSICS_COMPONENT_ORDER,
    )
    return entity_id


def create_canister_entity(gameworld: GameWorld, plan: CanisterPlan) -> int:
    """ Light body, drifting and spinning, which touches nothing """
    width, height = CANISTER_SIZE
    scale = display_scale(plan.mineral)
    entity_id: int = gameworld.init_entity(
        components_to_use={
            'cymunk_physics': {
                'main_shape': 'box',
                'position': plan.pos,
                'angle': plan.angle,
                'angular_velocity': plan.spin,
                'velocity': plan.velocity,
                'mass': 1.,
                'col_shapes': [{
                    'shape_type': 'box',
                    'elasticity': .5,
                    'collision_type': COLLISION_CANISTER,
                    'friction': 1.,
                    'shape_info': {
                        'width': width, 'height': height, 'mass': 1.,
                    },
                }],
            },
            'position': plan.pos,
            'rotate': 0,
            'rotate_renderer': {
                'texture': canister_texture(plan.mineral),
                'size': (width * scale, height * scale),
                'render': True,
            },
        },
        component_order=PHYSICS_COMPONENT_ORDER,
    )
    return entity_id


def create_star_entity(gameworld: GameWorld, pos: Vec2, size: float) -> Any:
    """ Returns the position component of the star """
    entity_id = gameworld.init_entity(
        components_to_use={
            'position': pos,
            'rotate': 0,
            'stars_renderer': {
                'texture': 'star',
                'size': (size, size),
                'render': True,
            },
        },
        component_order=['position', 'rotate', 'stars_renderer'],
    )
    return gameworld.entities[entity_id].position


def get_body(gameworld: GameWorld, entity_id: int) -> Body:
    return gameworld.entities[entity_id].cymunk_physics.body


def move_body(gameworld: GameWorld, entity_id: int, shift: Vec2) -> None:
    entity = gameworld.entities[entity_id]
    body = entity.cymunk_physics.body
    x, y = body.position.x + shift[0], body.position.y + shift[1]
    body.position = (x, y)
    # Static bodies don't update their position component
    entity.position.x, entity.position.y = x, y


def step_systems(gameworld: GameWorld, dt: float) -> None:
    """ Once, by the actual frame time """
    system_manager = gameworld.system_manager
    for system_id in SYSTEMS:
        system = system_manager[system_id]
        if not system.updateable or system.paused:
            continue
        if isinstance(system, Renderer):
            system.update(False, dt)
        else:
            system.update(dt)
