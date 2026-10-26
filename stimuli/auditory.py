"""공유 PTB 출력 장치에서 WAV를 준비·예약 재생한다. 공통 시각은 과제에서 전달."""

import wave


class AuditoryStimuli:
    def __init__(self, directory, consonants, max_duration=0.5, settings=None):
        from config import AUDIO_PLAYBACK

        # PTB를 명시적으로 선택해 조용히 다른 backend로 바뀌는 것을 방지한다.
        from psychopy.sound.backend_ptb import SoundPTB
        from psychopy.hardware.speaker.speaker_psychtoolbox import (
            PsychtoolboxSpeakerDevice,
        )

        self.Sound = SoundPTB
        self.Speaker = PsychtoolboxSpeakerDevice
        self.settings = settings or AUDIO_PLAYBACK
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
        self.stop()
        self.block_sounds = [
            self.Sound(
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

    def status(self, trial_index):
        raw = self.block_sounds[trial_index].statusDetailed or {}
        return {
            key: raw.get(key)
            for key in (
                "Active",
                "State",
                "RequestedStartTime",
                "StartTime",
                "StopTime",
                "XRuns",
            )
        }

    def stop(self):
        for item in self.block_sounds:
            item.stop()

    def check(self, win, kb, logger):
        """본검사 전 실제 청취 확인. 무음 상태에서 시각 과제만 진행하지 않는다."""
        from psychopy import core, visual, gui

        if not self.settings["check_before_session"]:
            logger.write(
                "audio_check", confirmed=False, skipped=True, device=self.speaker.name
            )
            return
        message = visual.TextStim(win, height=0.03, wrapWidth=1.1)
        while True:
            self.prepare_block(self.consonants)
            for i, letter in enumerate(self.consonants):
                message.text = f"Audio check: {letter}\nOutput: {self.speaker.name}\nListen for the spoken letter. ESC: quit"
                when = win.getFutureFlipTime(clock="ptb", targetTime=0.1)
                self.schedule(i, when)
                clock = core.Clock()
                while clock.getTime() < 0.8:
                    if kb.getKeys(keyList=["escape"], waitRelease=False):
                        self.stop()
                        raise KeyboardInterrupt
                    message.draw()
                    win.flip()
            self.stop()
            message.text = (
                f"Audio output: {self.speaker.name}\n\n"
                "Did you hear all eight spoken letters?\n"
                "SPACE: yes, continue\nR: replay\nD: choose output device\nESC: quit"
            )
            message.draw()
            win.flip()
            key = kb.waitKeys(keyList=["space", "r", "d", "escape"], waitRelease=False)[
                0
            ].name
            if key == "escape":
                raise KeyboardInterrupt
            if key == "space":
                logger.write(
                    "audio_check",
                    confirmed=True,
                    skipped=False,
                    device=self.speaker.name,
                )
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
