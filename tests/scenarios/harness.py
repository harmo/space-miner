""" Plays the game in a window, step after step, to check what the unit
tests can't reach: Kivy, KivEnt and the physics. Each scenario runs in a
process of its own, with its data in a temporary folder.

    scenario = Scenario('name')

    @scenario.step(1.)
    def lands() -> None:
        scenario.check(scenario.player.parking is not None, 'parked')

    scenario.run()
"""

import math
import os
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Callable
from typing import Any

from app.logic.world.space import Vec2

Step = Callable[[], None]
SETTLING = .3                 # seconds once the game has set itself up
SMALL_ROCK = 6.               # radius, mined within a few seconds
# Seconds a step may take on the clock, beyond the time it asks for: it is
# stuck past that, and takes its window down with it
STUCK = 30.


def loneliest(asteroids: list[Any]) -> Any:
    """ Of small rock, the farthest from the others: none to bump into,
    and quickly mined """
    rocks = [
        a for a in asteroids
        if (a.mineral or 'rock') == 'rock' and a.radius < SMALL_ROCK
    ]
    return max(rocks, key=lambda rock: min(
        math.dist(rock.pos, other.pos)
        for other in asteroids if other is not rock
    ))


def prepare() -> None:
    """ Before the window opens """
    if 'SPACE_MINER_DATA' not in os.environ:
        os.environ['SPACE_MINER_DATA'] = tempfile.mkdtemp('-space-miner')
    os.environ.setdefault('SPACE_MINER_WINDOW', '1280x720')
    # Always the same solar system
    os.environ.setdefault('SPACE_MINER_SEED', '1')
    # Sounds play all the same, without being heard
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    # Windows out of sight would wait for the screen, and the game hardly
    # move on: frames are cut to MAX_FRAME_TIME
    from kivy.config import Config
    Config.set('graphics', 'vsync', '0')


class Scenario:

    def __init__(self, name: str) -> None:
        prepare()
        # main.py sets the window up, before the game opens it
        import main  # noqa: F401
        from app.engine.app import SpaceMinerApp
        self.name = name
        self.app = SpaceMinerApp()
        self.steps: list[tuple[float, Step]] = []
        self.failures: list[str] = []
        self.finished = False     # all its steps played
        self.data = os.environ['SPACE_MINER_DATA']
        self.current = 'starting'           # what it is waiting for
        self.deadline = time.monotonic() + STUCK

    # Writing scenarios

    def step(self, delay: float) -> Callable[[Step], Step]:
        """ Runs `delay` seconds of the game after the previous step """
        def add(function: Step) -> Step:
            self.steps.append((delay, function))
            return function
        return add

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self.failures.append(message)
            print(f'  ✗ {message}', flush=True)

    def log(self, *values: object) -> None:
        print('   ', *values, flush=True)

    # The game

    @property
    def game(self) -> Any:
        return self.app.root

    @property
    def base(self) -> Any:
        return self.game.ids.base

    @property
    def player(self) -> Any:
        return self.game.player

    def press(self, widget: Any, at: Vec2 | None = None) -> None:
        """ A tap at the center of the widget, or `at` that point of the
        widget """
        from kivy.tests.common import UnitTestTouch
        x, y = widget.to_window(*(at or widget.center))
        touch = UnitTestTouch(x, y)
        touch.touch_down()
        touch.touch_up()

    def button(self, root: Any, text: str) -> Any:
        """ The button showing `text` among the widgets of `root` """
        for widget in root.walk():
            if getattr(widget, 'text', None) == text and hasattr(
                widget, 'glow'
            ):
                return widget
        raise LookupError(f'no button "{text}"')

    def record_sounds(self) -> list[str]:
        """ The names of the sounds played once, from now on """
        from app.engine.audio import audio
        played: list[str] = []
        play = audio.play

        def recording(name: str, volume: float | None = None) -> None:
            played.append(name)
            play(name, volume)
        audio.play = recording  # type: ignore[method-assign]
        return played

    def screenshot(self, name: str) -> None:
        """ Into SPACE_MINER_SHOTS, when set, to look at """
        folder = os.environ.get('SPACE_MINER_SHOTS')
        if folder:
            from kivy.core.window import Window
            Window.screenshot(os.path.join(folder, f'{self.name}-{name}.png'))

    def escape(self) -> None:
        from kivy.core.window import Window
        Window.dispatch('on_keyboard', 27, 0, '', [])

    def hold_towards(self, direction: float) -> Any:
        """ Presses the screen in `direction` from its center: the ship
        thrusts that way until the returned touch is released """
        from kivy.core.window import Window
        from kivy.tests.common import UnitTestTouch
        # Well inside the window, away from the buttons at the bottom
        reach = min(Window.width, Window.height) / 4
        touch = UnitTestTouch(
            Window.width / 2 + math.cos(direction) * reach,
            Window.height / 2 + math.sin(direction) * reach,
        )
        touch.touch_down()
        return touch

    def away_from_earth(self) -> float:
        x, y = self.player.ship.position
        ex, ey = self.game.system.earth.pos
        return math.atan2(y - ey, x - ex)

    def put_ship(self, pos: Vec2, velocity: Vec2,
                 angle: float | None = None) -> None:
        """ Moved by hand, flying """
        player = self.player
        player.parking = None
        body = player.ship.body
        body.position = pos
        body.velocity = velocity
        if angle is not None:
            body.angle = angle
        self.game.camera.look_at(pos)

    def above_earth(self, direction: float, height: float) -> Vec2:
        earth = self.game.system.earth
        distance = earth.radius + height
        return (
            earth.pos[0] + math.cos(direction) * distance,
            earth.pos[1] + math.sin(direction) * distance,
        )

    # Running

    def draw_nothing(self) -> None:
        """ Nobody sees it, and drawing without a graphics card would slow
        the game down. Unless pictures are wanted: the game then draws. """
        if not os.environ.get('SPACE_MINER_SHOTS'):
            from kivy.core.window import Window
            Window.bind(on_draw=lambda *_: True, on_flip=lambda *_: True)

    def watch(self) -> None:
        """ From a thread of its own, as the game may be what is stuck """
        while True:
            time.sleep(1.)
            if time.monotonic() > self.deadline:
                print(f'  ✗ stuck at {self.current}', flush=True)
                os._exit(1)

    def run(self) -> None:
        """ Exits with 1 when a check failed, a step raised, or the window
        closed before the end """
        from kivy.clock import Clock
        print(f'{self.name}', flush=True)
        threading.Thread(target=self.watch, daemon=True).start()

        def play(index: int) -> None:
            if index >= len(self.steps):
                self.finished = True
                self.app.stop()
                return
            delay, function = self.steps[index]
            self.current = function.__name__
            self.deadline = time.monotonic() + delay + STUCK
            # In the time of the game, which runs slower than the clock
            # when frames are long: they are cut to MAX_FRAME_TIME. That of
            # the clock while the game stands still.
            due, started = self.game.time + delay, time.monotonic()

            def run_step(dt: float) -> None:
                still = self.game.paused or self.game.map_open
                waited = time.monotonic() - started
                if self.game.time < due and not (still and waited >= delay):
                    return
                waiting.cancel()
                try:
                    function()
                except Exception:
                    self.failures.append(f'{function.__name__} raised')
                    traceback.print_exc()
                    self.app.stop()
                    return
                play(index + 1)
            waiting = Clock.schedule_interval(run_step, 0)

        def start(dt: float) -> None:
            self.game.playing = True
            play(0)

        def wait_for_the_game(dt: float) -> None:
            if self.game is not None and self.game.keeper is not None:
                ready.cancel()
                Clock.schedule_once(start, SETTLING)

        ready = Clock.schedule_interval(wait_for_the_game, 0)
        if os.environ.get('SPACE_MINER_UNSEEN'):
            self.draw_nothing()
        self.app.run()
        if not self.finished and not self.failures:
            self.failures.append('closed before the end')
            print('  ✗ the window closed before the end', flush=True)
        print('  ok' if not self.failures else '  FAILED', flush=True)
        sys.stdout.flush()
        # KivEnt crashes while Python tears it down, as main.py notes
        os._exit(1 if self.failures else 0)
