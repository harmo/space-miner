""" The shadow of the closest planet to the sun: out of it the hull heats
up and the sky is red, even more so during a flare, while behind the
planet no heat comes, the hull cools down and the sky is black """

import math
from typing import Any

from .harness import Scenario

scenario = Scenario('shadow')
check = scenario.check
remembered: dict[str, Any] = {}


def planet() -> Any:
    return scenario.game.system.planets[0]


def beside(distance: float) -> tuple[float, float]:
    """ Behind the planet seen from the sun, or before it if negative """
    sun, body = scenario.game.system.sun, planet()
    away = math.atan2(body.pos[1] - sun.pos[1], body.pos[0] - sun.pos[0])
    return (
        body.pos[0] + math.cos(away) * distance,
        body.pos[1] + math.sin(away) * distance,
    )


def sky() -> float:
    return float(scenario.game.sky.veil_color.a)


@scenario.step(1.)
def flies_on_the_side_of_the_sun() -> None:
    scenario.put_ship(beside(-planet().radius - 300), planet().velocity)
    scenario.player.heat.level = .4


@scenario.step(1.)
def heats_up_in_the_light() -> None:
    light = scenario.game.system.sunlight
    check(not light.shaded(scenario.player.ship.position), 'in the light')
    check(sky() > 0, f'the sky is red: {sky():.2f}')
    remembered['heat'] = scenario.player.heat.level
    check(remembered['heat'] > .4, f'heating up: {remembered["heat"]:.2f}')
    scenario.screenshot('light')
    scenario.put_ship(beside(planet().radius + 300), planet().velocity)


@scenario.step(1.)
def cools_down_behind_the_planet() -> None:
    light = scenario.game.system.sunlight
    check(light.shaded(scenario.player.ship.position), 'in its shadow')
    check(sky() == 0, f'the sky is black: {sky():.2f}')
    heat = scenario.player.heat.level
    check(heat < remembered['heat'], f'cooling down: {heat:.2f}')
    scenario.screenshot('shadow')


scenario.run()
