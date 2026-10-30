""" SDL_mixer, reached through ctypes for what Kivy lacks: looping a sound
seamlessly. Kivy restarts looping sounds once it notices they ended, up to
a tenth of a second late, which clicks. Loops play on channels of their
own, which Kivy never picks for its sounds. Uses the library Kivy loaded,
once it opened the audio device. """

import ctypes
import logging
from pathlib import Path

LOOP_CHANNELS = 4             # reserved for loops
CHANNELS = 16                 # in all, the others for Kivy's sounds
FULL = 128                    # volume of SDL_mixer

log = logging.getLogger(__name__)


def loaded_mixer() -> str | None:
    """ Path of SDL_mixer among the libraries loaded, where they are listed:
    on Linux and Android """
    maps = Path('/proc/self/maps')
    if not maps.exists():
        return None
    for line in maps.read_text().splitlines():
        if 'SDL2_mixer' in line:
            return line.split()[-1]
    return None


class Mixer:

    def __init__(self, library: ctypes.CDLL) -> None:
        self.library = library
        library.Mix_LoadWAV.argtypes = [ctypes.c_char_p]
        library.Mix_LoadWAV.restype = ctypes.c_void_p
        library.Mix_PlayChannel.argtypes = [
            ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
        ]
        self.chunks: dict[Path, int | None] = {}
        library.Mix_AllocateChannels(CHANNELS)
        library.Mix_ReserveChannels(LOOP_CHANNELS)

    def load(self, path: Path) -> int | None:
        """ Decoded once, None when it can't be """
        if path not in self.chunks:
            self.chunks[path] = self.library.Mix_LoadWAV(str(path).encode())
        return self.chunks[path]

    def loop(self, channel: int, path: Path) -> None:
        chunk = self.load(path)
        if chunk:
            self.library.Mix_PlayChannel(channel, chunk, -1)

    def volume(self, channel: int, volume: float) -> None:
        self.library.Mix_Volume(channel, round(volume * FULL))

    def halt(self, channel: int) -> None:
        self.library.Mix_HaltChannel(channel)

    def playing(self, channel: int) -> bool:
        return bool(self.library.Mix_Playing(channel))


def open_mixer() -> Mixer | None:
    """ None where SDL_mixer can't be found: Kivy loops sounds then """
    path = loaded_mixer()
    try:
        library = ctypes.CDLL(path or 'SDL2_mixer')
    except OSError:
        log.warning('SDL_mixer not found, loops may click')
        return None
    if not hasattr(library, 'Mix_LoadWAV'):
        return None
    return Mixer(library)
