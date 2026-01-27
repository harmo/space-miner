""" Plays every scenario, each in a process of its own: a window opens for
each of them.

    uv run python -m tests.scenarios.run [--phone] [name ...]

--phone plays them with the interface of phones, in a phone sized window.
Names pick scenarios, by part of their name.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
PHONE = {'SPACE_MINER_PLATFORM': 'android', 'SPACE_MINER_WINDOW': '960x432'}
TIMEOUT = 120                 # seconds for a scenario


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
    print(f'{"ok    " if passed else "FAILED"} {name}  ({seconds:.0f} s)')
    if not passed:
        # What the scenario said, then the end of what Kivy said
        lines = [line for line in result.stdout.splitlines() if line]
        print('\n'.join(lines), '\n'.join(result.stderr.splitlines()[-25:]),
              sep='\n')
    return passed


def main() -> None:
    arguments = sys.argv[1:]
    phone = '--phone' in arguments
    names = scenarios([name for name in arguments if name != '--phone'])
    results = [play(name, phone) for name in names]
    failed = results.count(False)
    print(f'\n{len(results) - failed} / {len(results)} scenarios passed')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
