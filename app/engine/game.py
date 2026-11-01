""" The game widget: sets KivEnt up and runs the game loop """

import os
from random import Random
from typing import Any, cast

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

from ..logic.base.board import Board
from ..logic.base.missions import Desk
from ..logic.base.outposts import Outpost, open_boards, site_desks
from ..logic.base.quays import Quay, shuttle_position, update_shuttles
from ..logic.base.sites import PERMITS
from ..logic.config import (
    AUTOSAVE_PERIOD,
    MAX_FRAME_TIME,
    MOBILE_PLATFORMS,
    SYSTEMS,
    WORLD_SIZE,
)
from ..logic.hud import heat_at, is_compact
from ..logic.ship.ground import Ground, Grounds
from ..logic.world.layout import plan_system
from ..logic.world.space import Celestial, Vec2
from .base.outposts import found_outposts
from .base.post_view import PostView
from .base.quays import quays_of
from .entities import setup_collisions, setup_state, step_systems
from .keeper import Keeper
from .ship.looks import ShipLooks
from .ship.player import Player
from .soundtrack import Soundtrack
from .storage import (
    delete_save,
    read_preferences,
    read_save,
    write_preferences,
)
from .textures import ground_edge, load_textures
from .ui.controls import escape, steers
from .ui.hud import show_hud
from .ui.map_view import Charted
from .ui.overlay import Overlay
from .ui.pointer import pointer_heading
from .ui.scene import SceneView, draw_scene
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
    outposts: list[Outpost]
    overlay: Overlay
    soundtrack: Soundtrack

    def on_kv_post(self, base_widget: Widget) -> None:
        self.rng = Random()
        self.time = 0.
        self.pointer: Vec2 | None = None
        self.pointer_uid: int | None = None
        self.preferences = read_preferences()
        self.slot = self.preferences.slot   # of the game behind the home
        self.chosen = False     # that game, or nothing is saved
        self.keeper: Keeper | None = None   # once the game is set up
        self.sun: Celestial | None = None   # of the previous game
        load_textures()
        Window.bind(on_keyboard=self.on_keyboard)
        # Once the kv file attached the systems to the game world, on the
        # next frame: earlier, KivEnt would wait a whole second for them
        Clock.schedule_once(lambda dt: self.gameworld.init_gameworld(
            SYSTEMS, callback=self.initialize,
        ))

    def initialize(self) -> None:
        setup_state(self.gameworld)
        self.sky = Sky(self.canvas.before)
        self.stars = StarField(self.gameworld)
        setup_collisions(self.gameworld, self.on_contact)
        self.soundtrack = Soundtrack(self.rng)
        self.open_world()
        Clock.schedule_interval(lambda dt: self.save(), AUTOSAVE_PERIOD)
        # Over the game world, under the widgets of the interface
        self.overlay = Overlay(self.gameworld.canvas.after, self.camera)
        self.ids.home.refresh(None)
        self.gameworld.state = 'main'
        # GameWorld steps each system on its own fixed 1/60s clock, doing 0,
        # 1 or 2 steps per frame which makes moving objects stutter. Step
        # everything once per frame with the actual frame time instead.
        Clock.unschedule(self.gameworld.update)
        Clock.schedule_interval(self.update, 0)

    def on_contact(self, space: Any, arbiter: Any) -> bool:
        return self.player.on_contact(space, arbiter)

    def open_world(self) -> None:
        """ The game of the slot, or a new one in a solar system of its
        own """
        save = read_save(self.slot)
        # The same solar system comes back with the saved game. Scenarios
        # pick theirs with SPACE_MINER_SEED.
        seed = save.seed if save else int(
            os.environ.get('SPACE_MINER_SEED') or self.rng.randrange(2 ** 31)
        )
        self.system = SolarSystem(
            self.gameworld, plan_system(Random(seed)),
            center=(WORLD_SIZE / 2, WORLD_SIZE / 2), rng=self.rng,
            sun=self.sun,
        )
        self.outposts = found_outposts(
            self.system, self.rng, self.ids.base.permits,
        )
        self.player = Player(
            self.gameworld, self.system, self.camera, self.rng,
            Grounds([
                Ground(self.system.earth, tuple(ground_edge('earth'))),
                *(outpost.ground for outpost in self.outposts),
            ]),
        )
        self.looks = ShipLooks(self.rng)  # its trail and legs
        self.soundtrack.listen(self.player)
        self.ids.base.setup(self.player, self.rng)
        self.ids.outpost.setup(self.player, self.outposts, self.ids.base)
        self.ids.base.outposts = self.outposts
        base = self.ids.base
        if base.board is not None:
            open_boards(self.outposts, base.wallet)
        self.ids.scanner.setup(self.player, self.system, lambda: self.desks)
        self.keeper = Keeper(
            seed, self.slot, self.player, self.ids.base, self.outposts,
        )
        if save is not None:
            self.keeper.restore(save)
        self.stars.wrap_all(self.player.anchor)

    def close_world(self) -> None:
        """ Its entities gone, the panels left with nothing of it """
        self.player.dispose()
        self.system.dispose()
        self.sun = self.system.sun
        self.ids.base.reset()
        self.ids.outpost.current = None
        self.keeper = None
        self.chosen = False

    @property
    def camera(self) -> Any:
        return self.gameworld.system_manager['camera1']

    @property
    def stop(self) -> PostView | None:
        """ The view of the post where the ship is landed, if any """
        for view in (self.ids.base, self.ids.outpost):
            if view.docked:
                return cast(PostView, view)
        return None

    @property
    def quays(self) -> list[Quay]:
        return quays_of(self.ids.base, self.outposts)

    @property
    def boards(self) -> list[Board]:
        """ Of the Earth and the outposts giving missions """
        boards = [self.ids.base.board]
        boards += [outpost.board for outpost in self.outposts]
        return [board for board in boards if board is not None]

    @property
    def desks(self) -> list[Desk]:
        """ Where missions are validated, the Earth first, with the
        concessions followed: a depot counts once, whatever it serves.
        Then the sites followed. """
        base = self.ids.base
        active = base.board.active if base.board is not None else []
        concessions = base.permits.tracked(PERMITS)
        return [Desk([*active, *concessions], base.depot.stock)] + [
            Desk(outpost.board.active, outpost.post.depot.stock)
            for outpost in self.outposts if outpost.board is not None
        ] + site_desks(self.outposts)

    # Game loop

    def update(self, dt: float) -> None:
        if self.paused or self.map_open:
            self.soundtrack.update(self, dt, None)
            self.draw_sky()         # filling the window if it changes
            return                  # everything stays as it was drawn
        dt = min(dt, MAX_FRAME_TIME)
        heading = pointer_heading(self.camera, self.pointer)
        self.player.update(dt, heading)
        self.looks.update(self.player, heading, dt)
        # Outposts first: those refuelling a ship landed there save it from
        # being stranded
        self.ids.outpost.update(dt)
        self.ids.base.update(dt)
        for board in self.boards:
            board.update(dt)
        update_shuttles(self.quays, dt)
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
        self.soundtrack.update(self, dt, heading)
        self.draw_sky()

    def draw_sky(self) -> None:
        anchor = self.player.anchor
        heat = 0. if self.system.sunlight.shaded(anchor) else heat_at(
            anchor, self.system.sun,
        )
        self.sky.draw(self.pos, self.size, self.camera, heat)

    def choose(self, slot: int) -> None:
        """ Plays its game, the one playing being saved first """
        if slot != self.slot:
            self.save()
            self.close_world()
            self.slot = slot
            self.open_world()
        self.preferences.slot = slot
        write_preferences(self.preferences)
        self.chosen = True
        self.resume()

    def erase(self, slot: int) -> None:
        """ That of the game behind the home page starts over """
        delete_save(slot)
        if slot == self.slot:
            self.close_world()
            self.open_world()
            self.paused = False
        self.ids.home.refresh(self.slot if self.paused else None)

    def pause(self) -> None:
        """ Back to the home page, the game frozen behind it """
        self.playing = False
        self.paused = True
        self.pointer = None
        self.draw_overlay()             # once more, without the markers
        self.save()
        self.ids.home.refresh(self.slot)

    def save(self) -> None:
        if self.keeper is not None and self.chosen:
            self.keeper.save()

    def open_settings(self) -> None:
        self.ids.settings.show(self.preferences)
        self.settings_open = True

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
            self.ids.outpost.close()
            self.ids.scanner.open = False
            self.pointer = None
            quays = self.quays
            shuttles = [shuttle_position(quay, quays) for quay in quays]
            self.ids.map.show(Charted(
                self.system, self.player, self.outposts,
                [pos for pos in shuttles if pos is not None],
            ))

    def toggle_cargo(self) -> None:
        self.cargo_open = not self.cargo_open

    def draw_overlay(self) -> None:
        draw_scene(self.overlay, self.size, SceneView(
            self.system, self.outposts, self.player, self.looks,
            self.playing, self.preferences,
        ))

    # Input

    def on_touch_down(self, touch: MotionEvent) -> bool:
        """ Thrusting towards the pointer while pressed, unless something
        is open over the game, or on the home page """
        ids = self.ids
        overlaid = ids.base.panel or ids.outpost.panel or ids.scanner.open
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
