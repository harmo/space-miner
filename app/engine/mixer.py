""" SDL_mixer, reached through ctypes for what Kivy lacks: looping a sound
seamlessly. Kivy restarts looping sounds once it notices they ended, up to
a tenth of a second late, which clicks. Loops play on channels of their
own, which Kivy never picks for its sounds. Uses the library Kivy loaded,
once it opened the audio device. Long sounds can be decoded aside, while
the game goes on, and freed once done with. """

import ctypes
import logging
import threading
from pathlib import Path

# Reserved for loops: two for the ambience fading, the engine, the laser
# and the unloading
LOOP_CHANNELS = 5
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
        library.Mix_FreeChunk.argtypes = [ctypes.c_void_p]
        self.chunks: dict[Path, int | None] = {}
        self.decoding: dict[Path, threading.Thread] = {}
        library.Mix_AllocateChannels(CHANNELS)
        library.Mix_ReserveChannels(LOOP_CHANNELS)

    def decode(self, path: Path) -> None:
        self.chunks[path] = self.library.Mix_LoadWAV(str(path).encode())

    def load(self, path: Path) -> int | None:
        """ Decoded once, None when it can't be. Waits for it when it is
        being decoded aside. """
        decoding = self.decoding.pop(path, None)
        if decoding is not None:
            decoding.join()
        if path not in self.chunks:
            self.decode(path)
        return self.chunks[path]

    def preload(self, path: Path) -> None:
        """ Decoded aside, so as not to hold the game up """
        if path not in self.chunks and path not in self.decoding:
            thread = threading.Thread(
                target=self.decode, args=(path,), daemon=True,
            )
            self.decoding[path] = thread
            thread.start()

    def free(self, path: Path) -> None:
        """ Once no channel plays it any more """
        chunk = self.load(path) if path in self.decoding else (
            self.chunks.get(path)
        )
        self.chunks.pop(path, None)
        if chunk:
            self.library.Mix_FreeChunk(chunk)

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
