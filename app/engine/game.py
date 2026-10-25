""" The game widget: sets KivEnt up and runs the game loop """

import os
from random import Random
from typing import Any

# Imported for their side effect: they register the widgets of the kv file
import kivent_core  # noqa: F401
import kivent_cymunk  # noqa: F401
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.input.motionevent import MotionEvent
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivy.utils import platform

from ..logic.config import (
    AUTOSAVE_PERIOD,
    MAX_FRAME_TIME,
    MOBILE_PLATFORMS,
    SYSTEMS,
    WORLD_SIZE,
)
from ..logic.hud import heat_at, is_compact
from ..logic.world.layout import plan_system
from ..logic.world.space import Vec2
from .entities import setup_collisions, setup_state, step_systems
from .keeper import Keeper
from .ship.looks import ShipLooks
from .ship.player import Player
from .storage import read_preferences, read_save
from .textures import ground_edge, load_textures
from .ui.controls import escape, steers
from .ui.hud import show_hud
from .ui.overlay import Overlay
from .ui.pointer import pointer_heading
from .ui.scene import draw_scene
from .world.sky import Sky
from .world.solar_system import SolarSystem
from .world.starfield import StarField
from .world.wrapping import recenter, wrap_space

ESCAPE = 27                   # also the back button on Android
MAP_KEY = 109                 # M

# Overrides the platform, to try the phone interface on a computer
PLATFORM = os.environ.get('SPACE_MINER_PLATFORM', platform)


class Game(Widget):

    gameworld = ObjectProperty(None)
    # On phones the cargo panel only shows when opened from a small button
    compact = BooleanProperty(False)
    cargo_open = BooleanProperty(False)
    # Outline of the landing shortcut, which glows when it can be used
    land_glow = NumericProperty(0.)
    # The home page shows until the game is played, and when it is paused
    playing = BooleanProperty(False)
    paused = BooleanProperty(False)
    settings_open = BooleanProperty(False)   # over the home page
    scanning = BooleanProperty(False)        # the ship has a scanner
    map_open = BooleanProperty(False)        # the game standing still
    mobile = BooleanProperty(PLATFORM in MOBILE_PLATFORMS)

    sky: Sky
    stars: StarField
    system: SolarSystem
    player: Player
    overlay: Overlay

    def on_kv_post(self, base_widget: Widget) -> None:
        self.rng = Random()
        self.time = 0.
        self.pointer: Vec2 | None = None
        self.pointer_uid: int | None = None
        self.looks = ShipLooks(self.rng)  # its trail and legs
        self.preferences = read_preferences()
        self.keeper: Keeper | None = None   # once the game is set up
        load_textures()
        Window.bind(on_keyboard=self.on_keyboard)
        self.gameworld.init_gameworld(SYSTEMS, callback=self.initialize)

    def initialize(self) -> None:
        setup_state(self.gameworld)
        self.sky = Sky(self.canvas.before)
        self.stars = StarField(self.gameworld)
        save = read_save()
        # The same solar system comes back with the saved game. Scenarios
        # pick theirs with SPACE_MINER_SEED.
        seed = save.seed if save else int(
            os.environ.get('SPACE_MINER_SEED') or self.rng.randrange(2 ** 31)
        )
        self.system = SolarSystem(
            self.gameworld, plan_system(Random(seed)),
            center=(WORLD_SIZE / 2, WORLD_SIZE / 2), rng=self.rng,
        )
        self.player = Player(
            self.gameworld, self.system, self.camera, self.rng,
            ground_edge('earth'),
        )
        setup_collisions(self.gameworld, self.player.on_contact)
        self.ids.base.setup(self.player, self.rng)
        self.ids.scanner.setup(self.player, self.system, self.ids.base)
        self.keeper = Keeper(seed, self.player, self.ids.base)
        if save is not None:
            self.keeper.restore(save)
        Clock.schedule_interval(lambda dt: self.save(), AUTOSAVE_PERIOD)
        # Over the game world, under the widgets of the interface
        self.overlay = Overlay(self.gameworld.canvas.after, self.camera)
        self.stars.wrap_all(self.player.anchor)
        self.gameworld.state = 'main'
        # GameWorld steps each system on its own fixed 1/60s clock, doing 0,
        # 1 or 2 steps per frame which makes moving objects stutter. Step
        # everything once per frame with the actual frame time instead.
        Clock.unschedule(self.gameworld.update)
        Clock.schedule_interval(self.update, 0)

    @property
    def camera(self) -> Any:
        return self.gameworld.system_manager['camera1']

    # Game loop

    def update(self, dt: float) -> None:
        if self.paused or self.map_open:
            self.draw_sky()         # filling the window if it changes
            return                  # everything stays as it was drawn
        dt = min(dt, MAX_FRAME_TIME)
        heading = pointer_heading(self.camera, self.pointer)
        self.player.update(dt, heading)
        self.looks.update(self.player, heading, dt)
        self.ids.base.update(dt)
        self.scanning = self.player.stats.scan > 0
        self.system.update(dt, self.player.anchor)
        shift = recenter(self.player, self.camera, self.system, self.stars)
        self.looks.shift(shift)
        self.sky.shift(shift)
        wrap_space(self.player, self.system, self.stars)
        step_systems(self.gameworld, dt)
        self.draw_overlay()
        self.time += dt
        self.compact = is_compact(
            PLATFORM, Window.width / dp(1), Window.height / dp(1)
        )
        show_hud(self)
        self.draw_sky()

    def draw_sky(self) -> None:
        self.sky.draw(
            self.pos, self.size, self.camera,
            heat_at(self.player.anchor, self.system.sun),
        )

    def play(self) -> None:
        """ Leave the home page """
        self.playing = True

    def pause(self) -> None:
        """ Back to the home page, the game frozen behind it """
        self.playing = False
        self.paused = True
        self.pointer = None
        self.draw_overlay()             # once more, without the markers
        self.save()

    def save(self) -> None:
        if self.keeper is not None:
            self.keeper.save()

    def open_settings(self) -> None:
        self.ids.settings.show(self.preferences)
        self.settings_open = True

    def new_game(self) -> None:
        if self.keeper is not None:
            self.keeper.new_game()
        self.settings_open = False

    def resume(self) -> None:
        self.paused = False
        self.playing = True

    def on_keyboard(self, window: Any, key: int, *args: Any) -> bool:
        """ Escape, or back on Android, closes what is open, pauses and
        resumes. M opens the map. """
        if key == MAP_KEY and self.playing:
            self.toggle_map()
            return True
        return key == ESCAPE and escape(self)

    def toggle_map(self) -> None:
        """ The game stands still behind it, closing what was open """
        self.map_open = not self.map_open
        if self.map_open:
            self.ids.base.close()
            self.ids.scanner.open = False
            self.pointer = None
            self.ids.map.show(self.system, self.player)

    def toggle_cargo(self) -> None:
        self.cargo_open = not self.cargo_open

    def draw_overlay(self) -> None:
        draw_scene(
            self.overlay, self.size, self.system, self.player, self.looks,
            self.playing, self.preferences,
        )

    # Input

    def on_touch_down(self, touch: MotionEvent) -> bool:
        """ Thrusting towards the pointer while pressed, unless something
        is open over the game, or on the home page """
        overlaid = self.ids.base.panel or self.ids.scanner.open
        if self.playing and not overlaid and not self.map_open and (
            steers(self, touch)
        ):
            self.pointer = touch.pos
            self.pointer_uid = touch.uid
        return bool(super().on_touch_down(touch))

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if touch.uid == self.pointer_uid:
            self.pointer = touch.pos
        return bool(super().on_touch_move(touch))

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.uid == self.pointer_uid:
            self.pointer = None
            self.pointer_uid = None
        return bool(super().on_touch_up(touch))
