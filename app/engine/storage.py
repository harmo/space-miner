""" Files of the player: the saved game and the preferences, in the data
folder of the application. Loads no window, to be read before it opens.
SPACE_MINER_DATA=folder keeps them elsewhere, for tests. """

import logging
import os
from pathlib import Path

from kivy.utils import platform

from ..logic.preferences import (
    Preferences,
    dump_preferences,
    load_preferences,
)
from ..logic.save import Save, SaveError, dump, load

NAME = 'spaceminer'
SAVE_FILE = 'save.json'
PREFERENCES_FILE = 'preferences.json'

log = logging.getLogger(__name__)


def data_dir() -> Path:
    """ Where applications keep their data on this platform """
    override = os.environ.get('SPACE_MINER_DATA')
    if override:
        path = Path(override)
    elif platform in ('android', 'ios'):
        from kivy.app import App
        path = Path(App.get_running_app().user_data_dir)
    elif platform == 'win':
        path = Path(os.environ['APPDATA']) / NAME
    elif platform == 'macosx':
        path = Path.home() / 'Library' / 'Application Support' / NAME
    else:
        config = os.environ.get('XDG_CONFIG_HOME')
        path = (Path(config) if config else Path.home() / '.config') / NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def write(name: str, text: str) -> None:
    """ Replaces the file at once: a crash while writing leaves the old
    one """
    path = data_dir() / name
    temporary = path.with_suffix('.tmp')
    temporary.write_text(text, encoding='utf-8')
    temporary.replace(path)


def read(name: str) -> str | None:
    path = data_dir() / name
    return path.read_text(encoding='utf-8') if path.exists() else None


def save_file(slot: int) -> str:
    return SAVE_FILE if slot == 1 else f'save_{slot}.json'


def read_save(slot: int) -> Save | None:
    """ None without one. One that can't be read is kept aside, and the
    game starts anew. """
    text = read(save_file(slot))
    if text is None:
        return None
    try:
        return load(text)
    except SaveError as error:
        path = data_dir() / save_file(slot)
        aside = path.with_suffix('.unreadable.json')
        path.replace(aside)
        log.warning('Unreadable saved game moved to %s: %s', aside, error)
        return None


def write_save(slot: int, save: Save) -> None:
    write(save_file(slot), dump(save))


def delete_save(slot: int) -> None:
    (data_dir() / save_file(slot)).unlink(missing_ok=True)


def saved_at(slot: int) -> float:
    """ Seconds since the epoch, 0 without a save """
    path = data_dir() / save_file(slot)
    return path.stat().st_mtime if path.exists() else 0.


def read_preferences() -> Preferences:
    text = read(PREFERENCES_FILE)
    return Preferences() if text is None else load_preferences(text)


def write_preferences(preferences: Preferences) -> None:
    write(PREFERENCES_FILE, dump_preferences(preferences))
