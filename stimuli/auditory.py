import wave
from config import AUDIO_PLAYBACK
from psychopy import sound, core, gui
from psychopy.hardware.speaker.speaker_psychtoolbox import PsychtoolboxSpeakerDevice

# Dual N-back의 청각 자극을 준비하고 재생 시점을 관리
class AuditoryStimuli:
    def __init__(self, directory, consonants, max_duration=0.5):
        # PTB 백엔드를 사용하여 오디오 재생 시점의 오차를 줄임
        sound.Sound.backend = "ptb"
        self.Speaker = PsychtoolboxSpeakerDevice
        self.settings = AUDIO_PLAYBACK
        self.directory = directory
        self.consonants = consonants
        self.block_sounds = []

        # 각 자음 음성이 설정된 자극 제시 시간(500ms)을 초과하지 않는지 확인
        for letter in consonants:
            path = directory / f"{letter}.wav"
            with wave.open(str(path)) as wav:
                duration = wav.getnframes() / wav.getframerate()
                if not 0 < duration <= max_duration + 0.0001:
                    raise ValueError(f"{path}: invalid audio duration ({duration}s).")

        # 모든 청각 자극이 동일한 출력 장치를 사용하도록 설정
        self.speaker = self.Speaker(name=self.settings["device_name"])

    # 블록에 사용할 음성을 미리 로딩하여 Trial 도중 발생하는 지연을 줄임
    def prepare_block(self, letters):
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

    # dual_nback.py에서 전달받은 시점에 맞춰 해당 Trial의 음성을 재생 예약
    def schedule(self, trial_index, when):
        self.block_sounds[trial_index].play(when=when)

    # 블록 종료 또는 실험 중단 시 재생 중인 모든 오디오 정지
    def stop(self):
        for item in self.block_sounds:
            item.stop()

    # 본 실험 시작 전 청각 자극의 발음과 출력 장치를 확인
    def check(self, win, kb, screens):
        if not self.settings["check_before_session"]:
            return

        while True:
            kb.clearEvents()
            self.prepare_block(self.consonants)

            # 8개 자음을 순서대로 재생하여 참가자가 음성을 확인하도록 함
            for i, letter in enumerate(self.consonants):
                # PTB 시간 기준으로 오디오 재생 시점을 미리 예약
                when = win.getFutureFlipTime(clock="ptb", targetTime=0.1)
                self.schedule(i, when)
                clock = core.Clock()

                # 각 자음을 확인하는 동안 화면을 갱신하고 키 입력도 확인
                while clock.getTime() < 0.8:
                    keys = kb.getKeys(keyList=["space", "escape"], waitRelease=False)

                    if any(key.name == "escape" for key in keys):
                        self.stop()
                        raise KeyboardInterrupt

                    # SPACE를 누르면 오디오 확인을 건너뛰고 본 실험으로 이동
                    if any(key.name == "space" for key in keys):
                        self.stop()
                        return

                    screens.draw_audio(letter, i)
                    win.flip()

            self.stop()

            # 전체 음성 확인 후 재청취, 출력 장치 변경 또는 실험 진행 선택
            key = screens.wait(kb, screens.draw_audio,
                               keys=("space", "r", "d", "escape"))

            if key == "space":
                return

            if key == "d":
                # 현재 사용 가능한 오디오 출력 장치 목록을 불러옴
                names = [d["deviceName"] for d in self.Speaker.getAvailableDevices()]
                choices = [self.speaker.name] + [
                    x for x in names if x != self.speaker.name
                ]

                selection = {"Output device": choices}

                # 선택한 출력 장치로 변경하여 이후 블록에서도 동일하게 사용
                if gui.DlgFromDict(selection, title="Select audio output").OK:
                    self.block_sounds = []
                    self.speaker = self.Speaker(name=selection["Output device"])
