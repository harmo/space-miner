""" Outposts founded in the solar system, on bodies of their own for those
it has none for """

from random import Random

from ...logic.base.outposts import Outpost, bare_outpost
from ...logic.world.layout import plan_ceres, plan_station
from ..world.solar_system import SolarSystem


def found_outposts(system: SolarSystem, rng: Random) -> list[Outpost]:
    """ On their sites, nothing built yet: the Frontier on the farthest
    planet, Cérès in the belt around the sun, and Icare orbiting the
    first planet, both added to the system """
    earth = system.earth.orbit
    ceres = system.add_body(plan_ceres(
        system.orbits, earth.angle if earth else 0.,
    ))
    first = system.planets[0]
    icare = system.add_body(plan_station(first.radius), first)
    return [
        bare_outpost(key, body, rng) for key, body in (
            ('frontier', system.planets[-1]), ('ceres', ceres),
            ('icare', icare),
        )
    ]
