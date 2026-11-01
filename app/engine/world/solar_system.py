""" The sun, the planets and their satellites, as KivEnt entities. Belts
mined out grow back, and swarms of rich asteroids pass by, see
events.py. """

import math
from collections.abc import Callable
from dataclasses import replace
from random import Random

from ...logic.config import (
    COLLISION_ORBITER,
    COLLISION_PLANET,
    COMET,
    PLANET_IMAGE_SCALE,
    SUN_DISC,
)
from ...logic.mining.minerals import display_scale
from ...logic.ship.heat import Sunlight
from ...logic.world.comets import CometOrbit
from ...logic.world.config import (
    COMET_RADIUS,
    MARS_ORBIT,
    ORBIT_PULL,
    PLANET_MASS,
    SUN_GRAVITY,
    SUN_GRAVITY_FALLOFF,
    SUN_RADIUS,
)
from ...logic.world.layout import BeltPlan, OrbiterPlan, SystemPlan, facing
from ...logic.world.shadow import shadow_of
from ...logic.world.space import Celestial, Orbit, Vec2, closest_to
from ..entities import (
    GameWorld,
    RoundBody,
    create_round_entity,
    get_body,
    move_body,
)
from .events import SystemEvents


class SolarSystem:

    def __init__(
        self,
        gameworld: GameWorld,
        plan: SystemPlan,
        center: Vec2,
        rng: Random,
        sun: Celestial | None = None
    ) -> None:
        """ With the `sun` of the previous one, if any, see dispose """
        self.gameworld = gameworld
        self.planets: list[Celestial] = []
        self.looks: list[str] = []          # textures of the planets
        self.asteroids: list[Celestial] = []
        # Parents always come before their satellites
        self.bodies: list[Celestial] = []
        self.locked: list[Celestial] = []   # facing their parent
        # The asteroids of each belt of the plan, mined or not
        self.belt_plans = list(plan.belts)
        self.orbits = plan.orbits           # of the planets and the belt
        self.belts: list[list[Celestial]] = [[] for _ in plan.belts]
        belt_of = {belt.parent: index for index, belt in enumerate(plan.belts)}
        self.planned: dict[Celestial, OrbiterPlan] = {}  # asteroids
        # Told when an asteroid goes, mined out or leaving with its swarm
        self.on_remove: list[Callable[[Celestial], None]] = []

        self.sun = self.place_sun(sun, center)
        for index, planet_plan in enumerate(plan.planets):
            planet = self.create_orbiter(
                planet_plan.planet, self.sun, COLLISION_PLANET
            )
            self.planets.append(planet)
            self.looks.append(planet_plan.planet.texture)
            for satellite_plan in planet_plan.satellites:
                if index == plan.earth:   # the moon
                    self.create_orbiter(
                        satellite_plan, planet, COLLISION_ORBITER
                    )
                else:
                    self.belts[belt_of[index]].append(
                        self.add_asteroid(satellite_plan, planet)
                    )
        for asteroid_plan in plan.sun_belt:
            self.belts[belt_of[None]].append(
                self.add_asteroid(asteroid_plan, self.sun)
            )
        # What the belts turn around
        self.belt_parents = [
            self.sun if belt.parent is None else self.planets[belt.parent]
            for belt in plan.belts
        ]
        self.earth = self.planets[plan.earth]
        self.attractors = [self.sun, *self.planets]
        self.events = SystemEvents(self, rng)

    @property
    def mercury(self) -> Celestial:
        """ The closest planet to the sun """
        return self.planets[0]

    @property
    def mars(self) -> Celestial:
        return self.planets[MARS_ORBIT]

    @property
    def neptune(self) -> Celestial:
        """ The farthest planet from the sun """
        return self.planets[-1]

    def add_body(
        self,
        plan: OrbiterPlan,
        parent: Celestial | None = None
    ) -> Celestial:
        """ Around `parent`, the sun without any, solid as the planets and
        pulling if it has gravity """
        body = self.create_orbiter(plan, parent or self.sun, COLLISION_PLANET)
        if plan.gravity:
            self.attractors.append(body)
        return body

    def add_belt(
        self,
        belt: BeltPlan,
        parent: Celestial,
        rng: Random
    ) -> None:
        """ Full, around `parent` """
        self.belt_parents.append(parent)
        self.belt_plans.append(belt)
        self.belts.append([
            self.add_asteroid(belt.asteroid(rng), parent)
            for _ in range(belt.full)
        ])
        self.events.watch(belt)

    def add_asteroid(
        self,
        plan: OrbiterPlan,
        parent: Celestial
    ) -> Celestial:
        asteroid = self.create_orbiter(plan, parent, COLLISION_ORBITER)
        self.asteroids.append(asteroid)
        self.planned[asteroid] = plan
        return asteroid

    def plan_now(self, asteroid: Celestial) -> OrbiterPlan:
        """ Of it as it is, on its orbit """
        assert asteroid.orbit is not None
        return replace(
            self.planned[asteroid], orbit_angle=asteroid.orbit.angle,
        )

    @property
    def sunlight(self) -> Sunlight:
        """ Surging during flares, the closest planet casting its shadow """
        sun, planet = self.sun, self.mercury
        return Sunlight(
            sun.pos, sun.radius, self.events.flares.surge,
            shadow_of(planet.pos, planet.radius, sun.pos),
        )

    def update(self, dt: float, ship: Vec2) -> None:
        """ Out of the sight of the ship, where it is now """
        self.move_orbiters(dt)
        self.events.update(dt, ship)

    def asteroid_at(self, pos: Vec2, tolerance: float) -> Celestial | None:
        return closest_to(pos, self.asteroids, tolerance)

    def remove(self, celestial: Celestial) -> None:
        self.bodies.remove(celestial)
        if celestial in self.asteroids:
            self.asteroids.remove(celestial)
            del self.planned[celestial]
        for belt in self.belts:
            if celestial in belt:
                belt.remove(celestial)
        self.gameworld.remove_entity(celestial.entity_id)
        for listener in self.on_remove:
            listener(celestial)

    def dispose(self) -> None:
        """ All of it gone, for the solar system of another game, but its
        sun: the physics engine can't remove a static body, and each game
        has the same one """
        for body in self.bodies[1:]:
            self.gameworld.remove_entity(body.entity_id)

    def place_sun(self, sun: Celestial | None, pos: Vec2) -> Celestial:
        """ That of the previous solar system, or a new one """
        if sun is None:
            return self.create_sun(pos)
        back = pos[0] - sun.pos[0], pos[1] - sun.pos[1]
        sun.shift(back)
        move_body(self.gameworld, sun.entity_id, back)
        physics = self.gameworld.system_manager['cymunk_physics']
        physics.space.reindex_static()
        self.bodies.append(sun)
        return sun

    def create_sun(self, pos: Vec2) -> Celestial:
        entity_id = create_round_entity(self.gameworld, RoundBody(
            'sun', pos, SUN_RADIUS, mass=0, collision_type=COLLISION_PLANET,
            display_radius=SUN_RADIUS / SUN_DISC,
        ))
        sun = Celestial(
            entity_id, SUN_RADIUS, pos=pos,
            gravity=SUN_GRAVITY, gravity_falloff=SUN_GRAVITY_FALLOFF,
            gravity_range=None,
        )
        self.bodies.append(sun)
        return sun

    def create_orbiter(
        self,
        plan: OrbiterPlan,
        parent: Celestial,
        collision_type: int
    ) -> Celestial:
        orbit = Orbit(parent, plan.orbit_radius, plan.speed, plan.orbit_angle)
        entity_id = create_round_entity(self.gameworld, RoundBody(
            plan.texture, orbit.position, plan.radius, plan.mass,
            collision_type, plan.rotation, orbit.velocity,
            math.radians(plan.spin),
            plan.radius * display_scale(plan.mineral)
            * PLANET_IMAGE_SCALE.get(plan.texture, 1.),
        ))
        celestial = Celestial(
            entity_id, plan.radius, orbit=orbit, gravity=plan.gravity,
            mineral=plan.mineral,
        )
        self.bodies.append(celestial)
        if plan.locked:
            self.locked.append(celestial)
        return celestial

    def add_comet(self, orbit: CometOrbit) -> Celestial:
        """ Going through the planets and whatever turns around them """
        entity_id = create_round_entity(self.gameworld, RoundBody(
            COMET, orbit.position, COMET_RADIUS, PLANET_MASS,
            COLLISION_ORBITER, velocity=orbit.velocity,
        ))
        comet = Celestial(entity_id, COMET_RADIUS, orbit=orbit)
        self.bodies.append(comet)
        return comet

    def move_orbiters(self, dt: float) -> None:
        """ Steer every orbiting body along its orbit, parents first so that
        satellites follow where their parent now is """
        for celestial in self.bodies:
            orbit = celestial.orbit
            if orbit is None:
                continue
            orbit.advance(dt)
            body = get_body(self.gameworld, celestial.entity_id)
            x, y = orbit.position
            vx, vy = orbit.velocity
            body.velocity = (
                vx + (x - body.position.x) * ORBIT_PULL,
                vy + (y - body.position.y) * ORBIT_PULL,
            )
            if celestial in self.locked:
                # Whatever bumped into it
                body.angle = facing(orbit.angle)
                body.angular_velocity = orbit.angular_speed

    def shift(self, shift: Vec2) -> None:
        """ Move the sun, the orbits follow it """
        self.sun.shift(shift)
        for celestial in self.bodies:
            move_body(self.gameworld, celestial.entity_id, shift)
        # Static shapes are not tracked by the physics space otherwise
        physics = self.gameworld.system_manager['cymunk_physics']
        physics.space.reindex_static()
