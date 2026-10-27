"""참가자 자료 없이 실제 PsychoPy에서 안내 화면을 캡처한다."""
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DISPLAY, NBACK_UI, DATA_DIR
from psychopy import visual
from stimuli.nback_ui import ParticipantScreens
from stimuli.visual import VisualStimuli, FeedbackDisplay

parser = argparse.ArgumentParser()
parser.add_argument("--fullscreen", action="store_true")
args = parser.parse_args()
out = DATA_DIR / "smoke" / ("ui_v5_fullscreen" if args.fullscreen else "ui_v5")
out.mkdir(parents=True, exist_ok=True)
win = visual.Window(size=DISPLAY["size"], units="height", fullscr=args.fullscreen, useRetina=True,
                    color=NBACK_UI["flow_background"])
screens = ParticipantScreens(win)


def save(name):
    win.flip()
    win.getMovieFrame(buffer="front")
    win.saveMovieFrames(str(out / (name + ".png")))


try:
    for name, draw in (
        ("welcome", screens.draw_welcome),
        ("audio_playing", lambda: screens.draw_audio("B", 0)),
        ("audio_confirm", screens.draw_audio),
        ("instructions", screens.draw_instructions),
        ("ready", screens.draw_ready),
        ("countdown", lambda: screens.draw_countdown(2, 1, 3)),
        ("break", lambda: screens.draw_summary(1, 2, 3, dict(visual=2, auditory=1), 10)),
        ("complete", lambda: screens.draw_summary(20, 3, 3, dict(visual=2, auditory=1))),
    ):
        draw()
        save(name)
    win.color = NBACK_UI["background"]
    win.flip()
    shapes = VisualStimuli(win, DISPLAY)
    feedback = FeedbackDisplay(win)
    shapes.draw(6)
    feedback.draw("N=2  |  Block 1/20  |  Trial 1/20",
                  {"visual": "Correct", "auditory": "Incorrect"})
    save("feedback")
    shapes.draw(6)
    feedback.draw("N=2  |  Block 1/20  |  Trial 2/20", {},
                  {"visual": "Incorrect", "auditory": "Correct"})
    save("feedback_no_response")
    print(f"UI previews saved: {out}")
finally:
    win.close()
