"""실제 숫자 음성과 실행 흐름 검사. 회상 입력은 오답으로 자동 대체하므로 참가자 자료가 아니다."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from psychopy import prefs

prefs.hardware["audioLib"] = ["ptb", "PTB"]
from psychopy import visual, __version__
from config import DATA_DIR
from tasks import digit_span
from utils.data_logger import DataLogger
from utils.span_ui import show

digit_span.pause = lambda win, text, kb: show(win, text)
digit_span.recall_digits = lambda win, kb: ([], 0.0, [])
win = visual.Window(size=(800, 600), units="height", color="black", fullscr=False)
try:
    for mode in ("forward", "backward"):
        log = DataLogger(
            DATA_DIR / "smoke",
            "AUTOMATED_SMOKE",
            "digit_span",
            "pretest",
            dict(psychopy=__version__, mode=mode, simulated_recall=True),
        )
        try:
            digit_span.run(win, log, 2008, mode)
            log.write("session_end", status="completed")
            print("DIGIT SMOKE PASSED", mode, log.path)
        except Exception as error:
            log.write("session_end", status="error", error=repr(error))
            raise
        finally:
            log.close()
finally:
    win.close()
