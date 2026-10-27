"""참가자 등록 → 선택한 검사 → 다음 단계 제안 → 종료·저장을 관리한다."""

import argparse
import csv
import re
from datetime import datetime, timezone
from pathlib import Path
import importlib
import secrets
import hashlib
from config import DATA_DIR, DISPLAY, NBACK_UI, PARTICIPANT_EMAIL_DOMAIN
from utils.data_logger import DataLogger, KST
from utils.native_window import enable_native_fullscreen


_LOCAL = re.compile(r"[a-z0-9][a-z0-9._%+-]*\Z", re.ASCII)


def normalize_hanyang_email(value):
    """입력한 이메일을 참가자 ID로 쓴다. 실제 계정 소유 확인은 하지 않는다."""
    email = str(value or "").strip().lower()
    local, separator, domain = email.partition("@")
    if (
        not separator
        or domain != PARTICIPANT_EMAIL_DOMAIN
        or len(local) > 64
        or len(email) > 254
        or not _LOCAL.fullmatch(local)
        or local.endswith(".")
        or ".." in local
    ):
        raise ValueError(f"Enter your Hanyang University email (@{PARTICIPANT_EMAIL_DOMAIN}).")
    return email


SPAN_TASKS = ("digit_span", "reading_span")
TASK_LABELS = {
    "digit_span": "Digit Span",
    "reading_span": "Reading Span",
    "dual_nback": "Dual N-back",
}


def latest_completed_pretest(directory, participant):
    """이메일이 같은 완료된 Pretest 중 가장 최근에 시작한 Span 검사."""
    candidates = []
    for path in Path(directory).glob("*_responses.csv"):
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle), None)
        except (OSError, UnicodeError, csv.Error):
            continue
        if (row and row.get("participant") == participant
                and row.get("phase") == "pretest"
                and row.get("task") in SPAN_TASKS
                and row.get("session_status") == "completed"):
            try:
                when = (datetime.strptime(row["recorded_kst"], "%Y-%m-%d %H:%M:%S")
                        .replace(tzinfo=KST) if row.get("recorded_kst") else
                        datetime.fromisoformat(row["recorded_utc"]))
                candidates.append((when.astimezone(timezone.utc), row["task"]))
            except (KeyError, ValueError):
                continue
    return max(candidates)[1] if candidates else None


def next_step(task, phase, selected_span):
    """완료된 단계의 다음 제안. 검사 하나만 선택한 Pre/Post 흐름."""
    if phase == "pretest" and task in SPAN_TASKS:
        return "dual_nback", "training"
    if task == "dual_nback" and phase == "training":
        return selected_span, "posttest"
    return None


def _choice(win, title, choices):
    from psychopy import visual
    from psychopy.hardware import keyboard

    kb = keyboard.Keyboard()

    def draw():
        win.color = "#FFFFFF"
        visual.Rect(win, width=3, height=3, fillColor="#FFFFFF",
                    lineColor="#FFFFFF").draw()
        visual.Rect(win, width=3, height=.12, pos=(0, .44),
                    fillColor="#292D32", lineColor="#292D32").draw()
        visual.TextStim(win, text="DUAL-N-BACK STUDY", color="#FFFFFF",
                        height=.035, pos=(0, .44)).draw()
        visual.TextStim(win, text=title, color="#292D32", height=.047,
                        wrapWidth=1.15, pos=(0, .09)).draw()
        width = min(.34, 1.18 / len(choices) - .02)
        for index, label in enumerate(choices.values()):
            x = (index - (len(choices) - 1) / 2) * (width + .02)
            visual.Rect(win, width=width, height=.085, pos=(x, -.23),
                        fillColor="#F3F4F3", lineColor="#DCE0DD").draw()
            visual.TextStim(win, text=label, color="#292D32", height=.020,
                            wrapWidth=width - .01, pos=(x, -.23)).draw()
    win._resize_draw = draw
    try:
        draw()
        win.callOnFlip(kb.clearEvents)
        win.flip()
        key = kb.waitKeys(keyList=list(choices), waitRelease=False)[0].name
        return key
    finally:
        win._resize_draw = None


def ask_continue(win, task, phase, next_task, next_phase):
    destination = TASK_LABELS[next_task] if next_task else "your chosen Span task"
    title = (f"{TASK_LABELS[task]} {phase.title()} complete.\n"
             f"Continue to {destination} {next_phase.title()}?")
    return _choice(win, title, {
        "space": "SPACE  Continue", "n": "N  Finish"
    }) == "space"


def choose_posttest_task(win):
    """Training만 단독 실행했을 때 대응할 Posttest 검사를 참가자가 고른다."""
    key = _choice(win, "Choose the Posttest task.", {
        "d": "D  Digit Span", "r": "R  Reading Span", "n": "N  Finish",
    })
    return {"d": "digit_span", "r": "reading_span"}.get(key)


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
    from psychopy import gui, visual

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
    task, phase = info["task"], info["phase"]
    selected_span = (task if task in SPAN_TASKS else
                     latest_completed_pretest(DATA_DIR, email))
    # 동일 참가자 Pre/Post는 동일 기반 seed에서 겹치지 않는 두 form을 생성한다.
    participant_seed = int.from_bytes(
        hashlib.sha256(email.encode()).digest()[:8], "big"
    )
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
            seed = (args.seed if args.seed is not None else
                    secrets.randbits(32) if task == "dual_nback" else participant_seed)
            logger = DataLogger(DATA_DIR, email, task, phase)
            completed = False
            try:
                win.color = NBACK_UI["background"] if task == "dual_nback" else DISPLAY["color"]
                module = importlib.import_module("tasks." + task)
                kwargs = dict(mode="forward") if task == "digit_span" else {}
                module.run(win, logger, seed, **kwargs)
                logger.write("session_end", status="completed")
                completed = True
            except KeyboardInterrupt:
                logger.write("session_end", status="aborted")
            except Exception:
                logger.write("session_end", status="error")
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
            win._resize_draw = None
            win.close()


if __name__ == "__main__":
    main()
