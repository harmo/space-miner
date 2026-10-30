""" Sounds played from their files, once or looping """

from pathlib import Path

from kivy.core.audio import Sound, SoundLoader

from ..logic.ambience import DRONES
from ..logic.config import SOUNDS
from ..logic.sounds import is_loop
from .mixer import LOOP_CHANNELS, Mixer, open_mixer


class Audio:

    def __init__(self) -> None:
        self.sounds: dict[str, Sound | None] = {}
        self.mixer: Mixer | None = None     # loops seamlessly, once open
        self.reserved = 0                   # channels given to loops
        self.volume = 1.                    # of the sounds played once

    def open(self) -> None:
        """ Loads every sound, but the drones of the ambience: too long to
        keep them all, they are loaded when about to play. Kivy opens the
        audio device with the first one: before the window, as SDL may
        hang opening it afterwards, with PulseAudio. """
        paths = [
            path for path in sorted(Path(SOUNDS).glob('*.ogg'))
            if path.stem not in DRONES
        ]
        for path in paths:
            if not is_loop(path.stem):
                self.sound(path.stem)
        self.mixer = open_mixer()
        for path in paths:
            if is_loop(path.stem):
                if self.mixer is not None:
                    self.mixer.load(path)
                else:
                    self.sound(path.stem)

    def preload(self, name: str) -> None:
        """ A loop about to play, decoded aside where the mixer can """
        if self.mixer is not None:
            self.mixer.preload(Path(SOUNDS) / f'{name}.ogg')

    def release(self, name: str) -> None:
        """ A sound no longer played, its memory freed """
        if self.mixer is not None:
            self.mixer.free(Path(SOUNDS) / f'{name}.ogg')
        sound = self.sounds.pop(name, None)
        if sound is not None:
            sound.unload()

    def sound(self, name: str) -> Sound | None:
        """ Loaded on first use, None when it can't be """
        if name not in self.sounds:
            self.sounds[name] = SoundLoader.load(f'{SOUNDS}/{name}.ogg')
        return self.sounds[name]

    def play(self, name: str, volume: float | None = None) -> None:
        """ At the volume of the sounds, unless told another one """
        volume = self.volume if volume is None else volume
        sound = self.sound(name) if volume > 0 else None
        if sound is not None:
            sound.volume = volume
            sound.play()

    def reserve(self) -> int | None:
        """ A channel of the mixer for a loop, None without any left """
        if self.mixer is None or self.reserved >= LOOP_CHANNELS:
            return None
        self.reserved += 1
        return self.reserved - 1


class Loop:
    """ One sound at a time, repeating itself: on a channel of the mixer, or
    by Kivy without any """

    def __init__(self, audio: Audio) -> None:
        self.audio = audio
        self.name: str | None = None
        self.channel = audio.reserve()

    def play(self, name: str | None, volume: float = 1.) -> None:
        """ Goes on with the same sound, switches to another one, or stops
        with none """
        if name != self.name:
            self.stop()
            self.name = name
            if name is not None:
                self.start(name, volume)
        elif name is not None:
            self.adjust(name, volume)

    def start(self, name: str, volume: float) -> None:
        mixer = self.audio.mixer
        if mixer is not None and self.channel is not None:
            mixer.volume(self.channel, volume)
            mixer.loop(self.channel, Path(SOUNDS) / f'{name}.ogg')
            return
        sound = self.audio.sound(name)
        if sound is not None:
            sound.loop = True
            sound.volume = volume
            sound.play()

    def adjust(self, name: str, volume: float) -> None:
        mixer = self.audio.mixer
        if mixer is not None and self.channel is not None:
            mixer.volume(self.channel, volume)
            return
        sound = self.audio.sound(name)
        if sound is not None:
            sound.volume = volume

    def stop(self) -> None:
        mixer = self.audio.mixer
        if mixer is not None and self.channel is not None:
            mixer.halt(self.channel)
        elif self.name is not None:
            sound = self.audio.sound(self.name)
            if sound is not None:
                sound.stop()
        self.name = None

    @property
    def playing(self) -> bool:
        mixer = self.audio.mixer
        if mixer is not None and self.channel is not None:
            return mixer.playing(self.channel)
        sound = self.audio.sound(self.name) if self.name else None
        return sound is not None and sound.state == 'play'


# Shared by the whole game, the buttons of the interface included
audio = Audio()
