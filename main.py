import logging
import os
import sys

from kivy.config import Config
from kivy.utils import platform

from app.engine.storage import read_preferences
from app.logic.config import MOBILE_PLATFORMS

# Must be set before the window is created (kivent_core creates it on import)
# SPACE_MINER_WINDOW=WIDTHxHEIGHT opens a window of that size instead
window = os.environ.get('SPACE_MINER_WINDOW')
if not window and platform not in MOBILE_PLATFORMS:
    if not read_preferences().fullscreen:
        window = '1280x720'
if window:
    width, height = window.split('x')
    Config.set('graphics', 'fullscreen', '0')
    Config.set('graphics', 'width', width)
    Config.set('graphics', 'height', height)
else:
    Config.set('graphics', 'fullscreen', 'auto')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# The audio device as well, or the game may hang opening it
from app.engine.audio import audio  # noqa: E402

audio.open()

from app.engine.app import SpaceMinerApp  # noqa: E402

if __name__ == '__main__':
    SpaceMinerApp().run()
    # KivEnt crashes while Python tears its objects down once the game is
    # over: leave right away instead, the system frees everything anyway
    logging.shutdown()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
