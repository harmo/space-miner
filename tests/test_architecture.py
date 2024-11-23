""" app.logic stays pure Python: app.engine builds on it, never the other
way around """

import ast
import subprocess
import sys
from pathlib import Path

LOGIC = Path(__file__).parent.parent / 'app' / 'logic'
ENGINES = ('kivy', 'kivent_core', 'kivent_cymunk', 'cymunk')


def imported_modules(path: Path) -> list[tuple[str, int]]:
    """ (module, relative level) of every import of a file """
    imports = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            imports += [(alias.name, 0) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.module or '', node.level))
    return imports


def logic_modules() -> list[Path]:
    return sorted(LOGIC.rglob('*.py'))


def test_logic_imports_neither_kivy_nor_the_engine() -> None:
    for path in logic_modules():
        # Relative imports climb up to app.logic at most
        depth = len(path.relative_to(LOGIC).parts)
        for module, level in imported_modules(path):
            assert level <= depth, f'{path.name} reaches out of app.logic'
            assert not module.startswith(('app.engine', *ENGINES)), (
                f'{path.name} imports {module}'
            )


def test_logic_loads_without_any_engine() -> None:
    # In a fresh interpreter, as the tests already loaded the modules here
    names = [
        '.'.join(path.relative_to(LOGIC).with_suffix('').parts)
        for path in logic_modules() if path.stem != '__init__'
    ]
    code = '; '.join([
        'import sys',
        *(f'import app.logic.{name}' for name in names),
        f'print([m for m in sys.modules if m.startswith({ENGINES!r})])',
    ])
    result = subprocess.run(
        [sys.executable, '-c', code], cwd=LOGIC.parent.parent,
        capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == '[]'
