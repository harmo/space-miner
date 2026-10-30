""" Sounds played from their files, once or looping. Muted, nothing plays,
and loops stop. """

from kivy.core.audio import Sound, SoundLoader

from ..logic.config import SOUNDS


class Audio:

    def __init__(self) -> None:
        self.sounds: dict[str, Sound | None] = {}
        self.muted = False

    def sound(self, name: str) -> Sound | None:
        """ Loaded on first use, None when it can't be """
        if name not in self.sounds:
            self.sounds[name] = SoundLoader.load(f'{SOUNDS}/{name}.wav')
        return self.sounds[name]

    def play(self, name: str) -> None:
        sound = None if self.muted else self.sound(name)
        if sound is not None:
            sound.play()


class Loop:
    """ One sound at a time, repeating itself """

    def __init__(self, audio: Audio) -> None:
        self.audio = audio
        self.name: str | None = None

    def play(self, name: str | None, volume: float = 1.) -> None:
        """ Goes on with the same sound, switches to another one, or stops
        with none """
        if self.audio.muted:
            name = None
        if name != self.name:
            self.stop()
            self.name = name
            sound = self.audio.sound(name) if name else None
            if sound is not None:
                sound.loop = True
                sound.volume = volume
                sound.play()
        elif name is not None:
            sound = self.audio.sound(name)
            if sound is not None:
                sound.volume = volume

    def stop(self) -> None:
        sound = self.audio.sound(self.name) if self.name else None
        if sound is not None:
            sound.stop()
        self.name = None


# Shared by the whole game, the buttons of the interface included
audio = Audio()
