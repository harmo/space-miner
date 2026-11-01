""" Plays every scenario, each in a process of its own, several at a time,
on a screen of their own which nobody sees: Xvfb draws them in software.

    uv run python -m tests.scenarios.run [--phone] [--one] [--visible]
        [name ...]

--phone plays them with the interface of phones, in a phone sized window.
--one plays them one after the other.
--visible opens their windows on the real screen, to watch them, which is
what happens without Xvfb.
Names pick scenarios, by part of their name.
"""

import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
PHONE = {'SPACE_MINER_PLATFORM': 'android', 'SPACE_MINER_WINDOW': '960x432'}
TIMEOUT = 120                 # seconds for a scenario
TOGETHER = 4                  # scenarios at a time
SCREEN = '1280x720x24'        # the unseen one


@contextmanager
def unseen_screen() -> Iterator[dict[str, str]]:
    """ What scenarios need to run on it, Xvfb telling its display """
    read, write = os.pipe()
    screen = subprocess.Popen(
        ['Xvfb', '-displayfd', str(write), '-screen', '0', SCREEN,
         '+extension', 'GLX', '-nolisten', 'tcp'],
        pass_fds=[write], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    os.close(write)
    display = os.read(read, 16).decode().strip()
    os.close(read)
    try:
        yield {
            'DISPLAY': f':{display}', 'SDL_VIDEODRIVER': 'x11',
            'LIBGL_ALWAYS_SOFTWARE': '1', 'SPACE_MINER_UNSEEN': '1',
        }
    finally:
        screen.terminate()
        screen.wait()


def scenarios(names: list[str]) -> list[str]:
    found = sorted(path.stem for path in HERE.glob('scenario_*.py'))
    if not names:
        return found
    return [name for name in found if any(part in name for part in names)]


def play(name: str, phone: bool, screen: dict[str, str]) -> bool:
    env = {**os.environ, **(PHONE if phone else {}), **screen}
    env.pop('SPACE_MINER_DATA', None)       # a fresh folder for each
    if screen:
        env.pop('WAYLAND_DISPLAY', None)
    started = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, '-m', f'tests.scenarios.{name}'], cwd=ROOT,
            env=env, capture_output=True, text=True, timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f'{name}: too long, over {TIMEOUT} s')
        return False
    passed = result.returncode == 0
    seconds = time.monotonic() - started
    print(f'{"ok    " if passed else "FAILED"} {name}  ({seconds:.0f} s)',
          flush=True)
    if not passed:
        # What the scenario said, then the end of what Kivy said
        lines = [line for line in result.stdout.splitlines() if line]
        print('\n'.join(lines), '\n'.join(result.stderr.splitlines()[-25:]),
              sep='\n')
    return passed


def main() -> None:
    arguments = sys.argv[1:]
    phone = '--phone' in arguments
    names = scenarios(
        [name for name in arguments if not name.startswith('--')]
    )
    started = time.monotonic()
    together = 1 if '--one' in arguments else TOGETHER

    def play_all(screen: dict[str, str]) -> list[bool]:
        with ThreadPoolExecutor(together) as pool:
            return list(pool.map(lambda n: play(n, phone, screen), names))

    if '--visible' in arguments or shutil.which('Xvfb') is None:
        results = play_all({})
    else:
        with unseen_screen() as screen:
            results = play_all(screen)
    failed = results.count(False)
    minutes, seconds = divmod(round(time.monotonic() - started), 60)
    print(f'\n{len(results) - failed} / {len(results)} scenarios passed'
          f' in {minutes} min {seconds:02d}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
