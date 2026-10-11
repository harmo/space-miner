""" The far sky slides behind the stars, slower than them, and reddens near
the sun """

import math
from typing import Any

from .harness import Scenario

scenario = Scenario('sky')
check = scenario.check
remembered: dict[str, Any] = {}


def corner() -> tuple[float, float]:
    """ Of the screen on the distant stars, in pixels of their image """
    layer = scenario.game.sky.layers[-1]
    u, v = layer.rectangle.tex_coords[:2]
    return u * layer.tile, v * layer.tile


def slid(before: float, after: float, tile: float) -> float:
    """ Along the image, which repeats """
    moved = abs(after - before) % tile
    return min(moved, tile - moved)


@scenario.step(1.)
def takes_off() -> None:
    scenario.screenshot('landed')
    remembered['corner'] = corner()
    remembered['anchor'] = scenario.player.anchor
    remembered['touch'] = scenario.hold_towards(scenario.away_from_earth())


@scenario.step(1.5)
def flies() -> None:
    scenario.screenshot('flying')
    remembered['touch'].touch_up()
    tile = scenario.game.sky.layers[-1].tile
    (x0, y0), (x1, y1) = remembered['corner'], corner()
    sky = math.hypot(slid(x0, x1, tile), slid(y0, y1, tile))
    travel = math.dist(remembered['anchor'], scenario.player.anchor)
    check(0 < sky < travel * .2,
          f'the sky slides slower than the ship: {sky:.0f} for {travel:.0f}')
    check(scenario.game.sky.veil_color.a == 0, 'not red far from the sun')
    sun = scenario.game.system.sun
    scenario.put_ship((sun.pos[0] + sun.radius + 800, sun.pos[1]), (900, 0))


@scenario.step(.2)
def near_the_sun() -> None:
    scenario.screenshot('sun')
    check(scenario.game.sky.veil_color.a > .3, 'reddened near the sun')


scenario.run()
