""" The map of the solar system: its orbits, planets and belts, the ship
with the reach of its scanner and what it finds, lost canisters, the
swarm passing by and the ejecta of a flare. Drawn once when opened, the
game standing still. """

import math
from dataclasses import dataclass
from typing import Any

from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Point, Rectangle, Triangle
from kivy.input.motionevent import MotionEvent
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

from ...logic.base.outposts import Outpost
from ...logic.colors import Rgb
from ...logic.config import (
    FLARE_COLOR,
    HOME_COLOR,
    OUTPOST_COLOR,
    PLANET_COLORS,
    RINGED,
    SUN_COLOR,
    SWARM_COLOR,
)
from ...logic.mining.minerals import MINERALS
from ...logic.ship.scanner import found, mineral_name
from ...logic.world.chart import ZOOMS, Chart, chart, zoomed
from ...logic.world.space import Vec2
from ..ship.player import Player
from ..world.solar_system import SolarSystem

FRAME_MARGIN = 20             # dp, above and below the round map
CANISTER_COLOR = (1., .6, .3)
SHADOW_MAP_COLOR = (1., 1., 1., .14)
SHIP_COLOR = (1., 1., 1.)


@dataclass(frozen=True)
class Charted:
    """ What the map shows """
    system: SolarSystem
    player: Player
    outposts: list[Outpost]


class MapView(Widget):

    zoom = NumericProperty(ZOOMS[0])

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.shown: Charted | None = None
        self.chart: Chart | None = None     # as drawn last

    def show(self, charted: Charted) -> None:
        self.shown = charted
        self.draw()

    def zoom_by(self, closer: bool) -> None:
        self.zoom = zoomed(self.zoom, closer)
        self.draw()

    def on_touch_down(self, touch: MotionEvent) -> bool:
        """ The mouse wheel zooms """
        if self.collide_point(*touch.pos) and touch.is_mouse_scrolling:
            self.zoom_by(touch.button == 'scrolldown')
            return True
        return bool(super().on_touch_down(touch))

    def draw(self) -> None:
        if self.shown is None:
            return
        system, player = self.shown.system, self.shown.player
        sun = system.sun
        farthest = max(
            planet.orbit.radius + planet.radius
            for planet in system.planets if planet.orbit
        )
        ship = player.ship.position if player.ship else None
        frame = chart(
            sun.pos, farthest, self.center,
            (self.width, self.height - 2 * dp(FRAME_MARGIN)),
            self.zoom, ship,
        )
        self.chart = frame
        self.canvas.clear()
        with self.canvas:
            self.orbits(system, frame)
            self.asteroids(system, player, frame)
            self.bodies(system, frame)
            self.lost(player, frame)
            self.swarm(system, frame)
            self.ejecta(system, frame)
            self.shadow(system, frame)
            self.outposts(self.shown.outposts, frame)
            self.ship(player, frame)

    def orbits(self, system: SolarSystem, frame: Chart) -> None:
        Color(1, 1, 1, .1)
        x, y = frame.place(system.sun.pos)
        for planet in system.planets:
            if planet.orbit:
                Line(circle=(x, y, frame.size(planet.orbit.radius)),
                     width=1)

    def asteroids(self, system: SolarSystem, player: Player,
                  frame: Chart) -> None:
        """ Faint dots, those the scanner finds in their color """
        Color(1, 1, 1, .25)
        Point(points=[
            value for asteroid in system.asteroids
            for value in frame.place(asteroid.pos)
        ], pointsize=dp(.8))
        ship = player.ship
        if ship is None or player.stats.scan <= 0:
            return
        spotted = found(
            system.asteroids, ship.position, player.stats.scan,
            player.looked_for, len(system.asteroids),
        )
        for name, mineral in MINERALS.items():
            points = [
                value for asteroid in spotted if mineral_name(asteroid) == name
                for value in frame.place(asteroid.pos)
            ]
            if points:
                Color(*mineral.color, 1)
                Point(points=points, pointsize=dp(1.8))

    def shadow(self, system: SolarSystem, frame: Chart) -> None:
        """ Where the sun can't reach, behind the closest planet """
        shadow = system.sunlight.shadow
        if shadow is not None:
            Color(*SHADOW_MAP_COLOR)
            Triangle(points=[
                value for pos in shadow for value in frame.place(pos)
            ])

    def bodies(self, system: SolarSystem, frame: Chart) -> None:
        self.disc(frame.place(system.sun.pos),
                  frame.size(system.sun.radius, dp(7)), SUN_COLOR)
        for planet, look in zip(system.planets, system.looks, strict=True):
            pos = frame.place(planet.pos)
            radius = frame.size(planet.radius, dp(4))
            self.disc(pos, radius, PLANET_COLORS[look])
            if look in RINGED:
                Color(*PLANET_COLORS[look], .7)
                Line(ellipse=(pos[0] - radius * 2, pos[1] - radius * .6,
                              radius * 4, radius * 1.2), width=1)
        earth = frame.place(system.earth.pos)
        Color(*HOME_COLOR, 1)
        Line(circle=(*earth, frame.size(system.earth.radius, dp(4)) + dp(4)),
             width=1.2)
        self.label('Terre', (earth[0], earth[1] - dp(16)), HOME_COLOR)

    def lost(self, player: Player, frame: Chart) -> None:
        """ Canisters of ore lost in crashes """
        Color(*CANISTER_COLOR, 1)
        side = dp(4)
        for canister in player.canisters.canisters:
            x, y = frame.place(canister.pos)
            Rectangle(pos=(x - side / 2, y - side / 2), size=(side, side))

    def swarm(self, system: SolarSystem, frame: Chart) -> None:
        spot = system.events.swarm_spot
        if spot is None:
            return
        x, y = frame.place(spot.pos)
        Color(*SWARM_COLOR, 1)
        Line(circle=(x, y, dp(9)), width=1.4)
        self.label('Essaim', (x, y + dp(18)), SWARM_COLOR)

    def ejecta(self, system: SolarSystem, frame: Chart) -> None:
        spot = system.events.flares.ejecta_spot
        if spot is None:
            return
        x, y = frame.place(spot.pos)
        Color(*FLARE_COLOR, 1)
        Line(circle=(x, y, dp(9)), width=1.4)
        self.label('Éjectas', (x, y + dp(18)), FLARE_COLOR)

    def outposts(self, outposts: list[Outpost], frame: Chart) -> None:
        """ A square on each site, outlined until something is built """
        side = dp(7)
        for outpost in outposts:
            x, y = frame.place(outpost.pos)
            Color(*OUTPOST_COLOR, 1)
            if outpost.construction.built:
                Rectangle(pos=(x - side / 2, y - side / 2), size=(side, side))
            else:
                Line(rectangle=(x - side / 2, y - side / 2, side, side),
                     width=1.2)
            self.label(outpost.name, (x, y + dp(16)), OUTPOST_COLOR)

    def ship(self, player: Player, frame: Chart) -> None:
        """ Pointing where it heads, within the reach of its scanner """
        ship = player.ship
        if ship is None:
            return
        x, y = frame.place(ship.position)
        if player.stats.scan > 0:
            Color(.6, .9, 1., .35)
            Line(circle=(x, y, frame.size(player.stats.scan)), width=1)
        angle = ship.body.angle
        points = []
        for turn, length in ((0., 9.), (2.5, 6.), (-2.5, 6.)):
            points += [
                x + math.cos(angle + turn) * dp(length),
                y + math.sin(angle + turn) * dp(length),
            ]
        Color(*SHIP_COLOR, 1)
        Triangle(points=points)

    def disc(self, pos: Vec2, radius: float, color: Rgb) -> None:
        Color(*color, 1)
        Ellipse(pos=(pos[0] - radius, pos[1] - radius),
                size=(2 * radius, 2 * radius))

    def label(self, text: str, pos: Vec2, color: Rgb) -> None:
        """ Centered on `pos` """
        label = CoreLabel(text=text, font_size=dp(12), bold=True)
        label.refresh()
        texture = label.texture
        Color(*color, 1)
        Rectangle(
            texture=texture, size=texture.size,
            pos=(pos[0] - texture.width / 2, pos[1] - texture.height / 2),
        )
