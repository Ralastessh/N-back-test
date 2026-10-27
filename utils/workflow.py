"""선택한 Span 검사 → Dual N-back → 같은 Span Posttest 안내."""

import csv
from datetime import datetime, timezone
from pathlib import Path
from utils.data_logger import KST

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
    win.callOnFlip(kb.clearEvents)
    win.flip()
    key = kb.waitKeys(keyList=list(choices), waitRelease=False)[0].name
    return key


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
