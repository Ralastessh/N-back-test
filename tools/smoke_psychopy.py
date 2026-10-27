"""연구 데이터와 분리된 자동 화면/음성 검사. 실제 타이밍 정확도를 검증하지 않는다."""

import sys
import argparse
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from psychopy import prefs

prefs.hardware["audioLib"] = ["ptb", "PTB"]
from psychopy import visual, __version__
from psychopy.hardware import keyboard
from config import DISPLAY, NBACK, DATA_DIR
from utils.data_logger import DataLogger
from tasks.dual_nback import run

RealKeyboard = keyboard.Keyboard


class AutoKeyboard:
    def __init__(self):
        self.real = RealKeyboard()
        self.armed = False
        self.audio_skip_sent = False
        self.clock = SimpleNamespace(reset=self.reset)
        from utils.sequence import generate_block
        from config import ASSUMPTIONS

        trials = generate_block(ASSUMPTIONS["start_n"], ASSUMPTIONS["consonants"], 2009)
        interval = NBACK["stimulus_s"] + NBACK["isi_s"]
        rt = ASSUMPTIONS["response_window_s"] - 0.3
        self.script = [
            (i * interval + rt, "a") for i, t in enumerate(trials) if not t.warmup
        ]

    def reset(self):
        self.real.clock.reset()
        self.armed = True

    def clearEvents(self):
        return self.real.clearEvents()

    def getKeys(self, **kwargs):
        result = self.real.getKeys(**kwargs)
        if args.scripted_responses:
            result = [key for key in result if key.name == "escape"]
        if args.scripted_responses and self.armed:
            now = self.real.clock.getTime()
            while self.script and self.script[0][0] <= now:
                timestamp, key = self.script.pop(0)
                result.append(SimpleNamespace(name=key, rt=timestamp))
        if args.audio_skip_check and not self.audio_skip_sent and "space" in kwargs.get("keyList", []):
            self.audio_skip_sent = True
            result.append(SimpleNamespace(name="space", rt=0.0))
        return result

    def waitKeys(self, **kwargs):
        return [type("Key", (), {"name": "space"})()]


keyboard.Keyboard = AutoKeyboard
# 소리 500ms는 유지하고 ISI만 100ms로 단축한 기술 검사.
parser = argparse.ArgumentParser()
parser.add_argument(
    "--full-timing", action="store_true", help="500ms+2500ms 실제 제시 간격 검사"
)
parser.add_argument(
    "--scripted-responses",
    action="store_true",
    help="Inject visual responses near each deadline (technical test only).",
)
parser.add_argument(
    "--preview",
    action="store_true",
    help="Save an English feedback screen after timing tests.",
)
parser.add_argument("--fullscreen", action="store_true")
parser.add_argument("--blocks", type=int, default=1)
parser.add_argument("--audio-skip-check", action="store_true",
                    help="Inject SPACE during audio check; does not confirm audibility.")
args = parser.parse_args()
if args.blocks < 1:
    parser.error("--blocks must be at least 1")
NBACK["blocks"] = args.blocks
if not args.full_timing:
    NBACK["isi_s"] = 0.1
import config

# Automated tests cannot confirm human audibility.
config.AUDIO_PLAYBACK["check_before_session"] = args.audio_skip_check

if not args.full_timing:
    config.ASSUMPTIONS["response_window_s"] = 0.6
log = DataLogger(
    DATA_DIR / "smoke",
    "AUTOMATED_SMOKE",
    "dual_nback",
    "technical_check",
    dict(
        psychopy=__version__,
        note="automated; not research data",
        full_timing=args.full_timing,
        scripted_responses=args.scripted_responses,
        blocks=args.blocks, audio_skip_check=args.audio_skip_check, fullscreen=args.fullscreen,
    ),
)
win = None
try:
    win = visual.Window(size=(800, 600), units="height", color=config.NBACK_UI["background"], fullscr=args.fullscreen, useRetina=True)
    run(win, log, 2008)
    log.write("session_end", status="completed")
    if args.preview:
        from stimuli.visual import VisualStimuli, FeedbackDisplay

        win.color = config.NBACK_UI["background"]
        win.flip()
        VisualStimuli(win, DISPLAY).draw(0)
        FeedbackDisplay(win).draw(
            "N=2  |  Block 1/20  |  Trial 1/20",
            {"visual": "Correct", "auditory": "Incorrect"},
        )
        win.flip()
        win.getMovieFrame(buffer="front")
        win.saveMovieFrames(str(DATA_DIR / "smoke" / "feedback_preview.png"))
    print("SMOKE PASSED", __version__, log.path)
except KeyboardInterrupt:
    log.write("session_end", status="aborted")
    raise
except Exception as error:
    log.write("session_end", status="error", error=repr(error))
    raise
finally:
    if win:
        win.close()
    log.close()
