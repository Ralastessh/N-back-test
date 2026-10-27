"""Coder에서 이 파일을 실행. 터미널에서는 --task로 과제 선택."""

import argparse
import importlib
import platform
import secrets
import hashlib
import sys
from config import (
    ROOT,
    PROTOCOL_VERSION,
    DATA_DIR,
    DISPLAY,
    NBACK,
    ASSUMPTIONS,
    AUDIO_DIR,
    AUDIO_GENERATION,
    AUDIO_PLAYBACK,
    NBACK_FEEDBACK,
    NBACK_UI,
    DIGIT_SPAN,
    READING_SPAN,
    require_decisions,
    PARTICIPANT_EMAIL_DOMAIN,
)
from utils.data_logger import DataLogger
from utils.participant import normalize_hanyang_email
from utils.native_window import enable_native_fullscreen
from utils.workflow import (
    ask_continue, choose_posttest_task, latest_completed_pretest, next_step,
    SPAN_TASKS,
)


def task_phase_error(task, phase):
    if task == "dual_nback" and phase != "training":
        return "Dual N-back requires Training. Please choose again."
    if task in ("digit_span", "reading_span") and phase not in ("pretest", "posttest"):
        return "Digit Span and Reading Span require Pretest or Posttest. Please choose again."
    return None


def main(default_task=None):
    parser = argparse.ArgumentParser(description="Jaeggi 2008 PsychoPy replication")
    parser.add_argument(
        "--task",
        choices=["dual_nback", "digit_span", "reading_span"],
        default=default_task,
    )
    parser.add_argument("--email", "--participant", dest="email",
                        help=f"Hanyang University email (@{PARTICIPANT_EMAIL_DOMAIN})")
    parser.add_argument("--phase", choices=["training", "pretest", "posttest"])
    parser.add_argument("--seed", type=int, default=None)
    screen = parser.add_mutually_exclusive_group()
    screen.add_argument("--fullscreen", dest="fullscreen", action="store_true")
    screen.add_argument("--windowed", dest="fullscreen", action="store_false")
    parser.set_defaults(fullscreen=None)
    args = parser.parse_args()
    # sound 모듈을 불러오기 전에 PTB를 선택한다.
    from psychopy import prefs

    prefs.hardware["audioLib"] = ["ptb", "PTB"]
    from psychopy import gui, visual, __version__

    tasks = ("dual_nback", "digit_span", "reading_span")
    phases = ("training", "pretest", "posttest")
    info = dict(email=args.email or "", task=args.task or tasks[0],
                phase=args.phase or phases[0])
    show_selection = not (args.email and args.task and args.phase)
    while True:
        if show_selection:
            # DlgFromDict는 선택지 목록을 선택된 문자열로 바꾸므로 매번 다시 만든다.
            dialog_info = dict(
                email=info["email"],
                task=[info["task"]] + [item for item in tasks if item != info["task"]],
                phase=[info["phase"]] + [item for item in phases if item != info["phase"]],
            )
            if not gui.DlgFromDict(dialog_info, title="Hanyang participant sign-in").OK:
                return
            info = dialog_info
        try:
            email = normalize_hanyang_email(info["email"])
        except ValueError as error:
            message, title = str(error), "Check university email"
        else:
            message = task_phase_error(info["task"], info["phase"])
            title = "Check task and phase"
        if message is None:
            break
        warning = gui.Dlg(title=title)
        warning.addText(message)
        warning.show()
        show_selection = True
    info["participant"] = email
    task, phase = info["task"], info["phase"]
    selected_span = (task if task in SPAN_TASKS else
                     latest_completed_pretest(DATA_DIR, email))
    # 동일 참가자 Pre/Post는 동일 기반 seed에서 겹치지 않는 두 form을 생성한다.
    participant_seed = int.from_bytes(
        hashlib.sha256(email.encode()).digest()[:8], "big"
    )
    digit_mode = "forward"
    display_settings = dict(DISPLAY, fullscr=(
        DISPLAY["fullscr"] if args.fullscreen is None else args.fullscreen
    ))
    win = None
    try:
        win = visual.Window(
            **{k: display_settings[k] for k in ("size", "fullscr", "units", "color", "useRetina")},
            allowGUI=True,
            infoMsg="Waiting...",
        )
        enable_native_fullscreen(win)
        while True:
            settings = {
                "dual_nback": ASSUMPTIONS,
                "digit_span": DIGIT_SPAN,
                "reading_span": READING_SPAN,
            }[task]
            require_decisions(settings, task)
            seed = (args.seed if args.seed is not None else
                    secrets.randbits(32) if task == "dual_nback" else participant_seed)
            logger = DataLogger(
                DATA_DIR, email, task, phase,
                dict(
                    seed=seed,
                    protocol_version=PROTOCOL_VERSION,
                    psychopy=__version__,
                    python=sys.version,
                    platform=platform.platform(),
                    paper=NBACK,
                    assumptions=ASSUMPTIONS,
                    audio_generation=AUDIO_GENERATION,
                    audio_playback=AUDIO_PLAYBACK,
                    nback_feedback=NBACK_FEEDBACK,
                    nback_ui=NBACK_UI,
                    stimulus_hashes={
                        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in list(AUDIO_DIR.rglob("*.wav"))
                        + [ROOT / READING_SPAN["sentence_file"]]
                        if path.is_file()
                    },
                    display=display_settings,
                    digit_span=DIGIT_SPAN,
                    reading_span=READING_SPAN,
                    mode=digit_mode if task == "digit_span" else None,
                ),
            )
            completed = False
            try:
                win.color = NBACK_UI["background"] if task == "dual_nback" else DISPLAY["color"]
                logger.write("display_runtime", fullscr=win.fullscr,
                             framebuffer_pixels=list(map(int, win.size)), use_retina=win.useRetina)
                module = importlib.import_module("tasks." + task)
                kwargs = dict(mode=digit_mode) if task == "digit_span" else {}
                module.run(win, logger, seed, **kwargs)
                logger.write("session_end", status="completed")
                completed = True
            except KeyboardInterrupt:
                logger.write("session_end", status="aborted")
            except Exception as error:
                logger.write("session_end", status="error", error=repr(error))
                raise
            finally:
                logger.close()
                print(f"Data saved: {logger.path}")
            if not completed:
                break
            following = next_step(task, phase, selected_span)
            if following is None or not ask_continue(win, task, phase, *following):
                break
            task, phase = following
            if task is None:
                task = choose_posttest_task(win)
                if task is None:
                    break
            if task in SPAN_TASKS:
                selected_span = task
    finally:
        if win is not None:
            win.close()


if __name__ == "__main__":
    main()
