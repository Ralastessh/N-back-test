"""공유 PTB 출력 장치에서 WAV를 준비·예약 재생한다. 공통 시각은 과제에서 전달."""

import wave


class AuditoryStimuli:
    def __init__(self, directory, consonants, max_duration=0.5):
        from config import AUDIO_PLAYBACK

        # PTB를 명시적으로 선택해 조용히 다른 backend로 바뀌는 것을 방지한다.
        from psychopy import sound
        from psychopy.hardware.speaker.speaker_psychtoolbox import (
            PsychtoolboxSpeakerDevice,
        )

        sound.Sound.backend = "ptb"
        self.Speaker = PsychtoolboxSpeakerDevice
        self.settings = AUDIO_PLAYBACK
        self.directory = directory
        self.consonants = consonants
        self.block_sounds = []
        for letter in consonants:
            path = directory / f"{letter}.wav"
            with wave.open(str(path)) as wav:
                duration = wav.getnframes() / wav.getframerate()
                if not 0 < duration <= max_duration + 0.0001:
                    raise ValueError(f"{path}: invalid audio duration ({duration}s).")
        self.speaker = self.Speaker(name=self.settings["device_name"])

    def prepare_block(self, letters):
        from psychopy import sound

        self.stop()
        self.block_sounds = [
            sound.Sound(
                str(self.directory / f"{letter}.wav"),
                preBuffer=-1,
                speaker=self.speaker,
                volume=self.settings["volume"],
                autoLog=False,
            )
            for letter in letters
        ]

    def schedule(self, trial_index, when):
        self.block_sounds[trial_index].play(when=when)

    def stop(self):
        for item in self.block_sounds:
            item.stop()

    def check(self, win, kb, screens):
        """SPACE는 건너뛰기, R은 다시 듣기, D는 출력 장치 변경."""
        from psychopy import core, gui

        if not self.settings["check_before_session"]:
            return
        while True:
            kb.clearEvents()
            self.prepare_block(self.consonants)
            for i, letter in enumerate(self.consonants):
                when = win.getFutureFlipTime(clock="ptb", targetTime=0.1)
                self.schedule(i, when)
                clock = core.Clock()
                while clock.getTime() < 0.8:
                    keys = kb.getKeys(keyList=["space", "escape"], waitRelease=False)
                    if any(key.name == "escape" for key in keys):
                        self.stop()
                        raise KeyboardInterrupt
                    if any(key.name == "space" for key in keys):
                        self.stop()
                        return
                    screens.draw_audio(letter, i)
                    win.flip()
            self.stop()
            key = screens.wait(kb, screens.draw_audio,
                               keys=("space", "r", "d", "escape"))
            if key == "space":
                return
            if key == "d":
                names = [d["deviceName"] for d in self.Speaker.getAvailableDevices()]
                choices = [self.speaker.name] + [
                    x for x in names if x != self.speaker.name
                ]
                selection = {"Output device": choices}
                if gui.DlgFromDict(selection, title="Select audio output").OK:
                    self.block_sounds = []
                    self.speaker = self.Speaker(name=selection["Output device"])
