""" Plays every scenario, each in a process of its own, several at a time:
a window opens for each of them.

    uv run python -m tests.scenarios.run [--phone] [--one] [name ...]

--phone plays them with the interface of phones, in a phone sized window.
--one plays them one after the other, to watch them.
Names pick scenarios, by part of their name.
"""

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
PHONE = {'SPACE_MINER_PLATFORM': 'android', 'SPACE_MINER_WINDOW': '960x432'}
TIMEOUT = 120                 # seconds for a scenario
TOGETHER = 4                  # scenarios at a time


def scenarios(names: list[str]) -> list[str]:
    found = sorted(path.stem for path in HERE.glob('scenario_*.py'))
    if not names:
        return found
    return [name for name in found if any(part in name for part in names)]


def play(name: str, phone: bool) -> bool:
    env = {**os.environ, **(PHONE if phone else {})}
    env.pop('SPACE_MINER_DATA', None)       # a fresh folder for each
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
    with ThreadPoolExecutor(1 if '--one' in arguments else TOGETHER) as pool:
        results = list(pool.map(lambda name: play(name, phone), names))
    failed = results.count(False)
    minutes, seconds = divmod(round(time.monotonic() - started), 60)
    print(f'\n{len(results) - failed} / {len(results)} scenarios passed'
          f' in {minutes} min {seconds:02d}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
