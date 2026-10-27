"""사용자 지정 청각 숫자 폭 검사. WAIS 원본 검사가 아니다."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DIGIT_SPAN, AUDIO_DIR
import random
from utils.scoring import span_summary
from utils.scoring import score_recall
from utils.span_ui import show, pause



def digit_plans(seed, settings):
    """Pre/Post·방향·연습/본시행을 같은 seed로 생성하되 숫자열 중복은 막는다."""
    rng = random.Random(f"digit:{seed}")
    used, plans = set(), {}
    for phase in ("pretest", "posttest"):
        for mode in ("forward", "backward"):
            for stage in ("practice", "test"):
                lengths = (
                    settings[mode + "_lengths"][:1] * settings["practice_trials"]
                    if stage == "practice"
                    else [
                        n
                        for n in settings[mode + "_lengths"]
                        for _ in range(settings["trials_per_length"])
                    ]
                )
                sequences = []
                for length in lengths:
                    for _ in range(10000):
                        digits = []
                        for _ in range(length):
                            candidates = [
                                str(d)
                                for d in settings["digit_pool"]
                                if settings["adjacent_repetitions"]
                                or not digits
                                or str(d) != digits[-1]
                            ]
                            if not candidates:
                                raise ValueError("No eligible digit candidates.")
                            digits.append(rng.choice(candidates))
                        key = tuple(digits)
                        if key not in used:
                            break
                    else:
                        raise ValueError(
                            "Cannot generate unique sequences with these settings."
                        )
                    used.add(key)
                    sequences.append(digits)
                plans[(phase, mode, stage)] = sequences
    return plans

def expected_recall(digits, mode):
    if mode not in ("forward", "backward"):
        raise ValueError("Choose forward or backward.")
    return list(digits) if mode == "forward" else list(reversed(digits))


def wait_until(clock, deadline, kb):
    from psychopy import core

    while clock.getTime() < deadline:
        if kb.getKeys(keyList=["escape"], waitRelease=False):
            raise KeyboardInterrupt
        core.wait(0.001)


def recall_digits(win, kb):
    from psychopy import core

    win.callOnFlip(kb.clearEvents)
    win.callOnFlip(kb.clock.reset)
    show(
        win, "Type the digits in the requested order.\nBACKSPACE: edit | ENTER: submit"
    )
    response = []
    events = []
    while True:
        for key in kb.getKeys(waitRelease=False, clear=True):
            events.append(dict(key=key.name, rt=key.rt))
            if key.name == "escape":
                raise KeyboardInterrupt
            if key.name in ("return", "num_enter"):
                return response, key.rt, events
            if key.name == "backspace":
                response = response[:-1]
            elif key.name in list("123456789"):
                response.append(key.name)
            show(win, " ".join(response) + "\n\nENTER: submit | BACKSPACE: edit")
        core.wait(0.001)


def run(win, logger, seed, mode="forward"):
    from psychopy import core, sound
    import psychtoolbox as ptb
    from psychopy.hardware import keyboard

    kb = keyboard.Keyboard()
    plans = digit_plans(seed, DIGIT_SPAN)
    if DIGIT_SPAN["presentation"] != "auditory":
        raise ValueError("This task supports auditory presentation only.")
    audio = {
        d: sound.Sound(
            str(AUDIO_DIR / DIGIT_SPAN["audio_subdir"] / f"{d}.wav"), preBuffer=-1
        )
        for d in DIGIT_SPAN["digit_pool"]
    }
    if any(s.getDuration() > DIGIT_SPAN["digit_interval_s"] for s in audio.values()):
        raise ValueError("A digit recording is longer than the presentation interval.")
    direction = "in the same order" if mode == "forward" else "in reverse order"
    try:
        for stage in ("practice", "test"):
            pause(win, f"Digit Span {mode}: {stage}\nEnter the digits {direction}.", kb)
            results = []
            failed = 0
            previous = None
            sequences = plans[(logger.phase, mode, stage)]
            for trial_index, digits in enumerate(sequences):
                length = len(digits)
                if length != previous:
                    failed = 0
                previous = length
                # RT 기준이 되는 실제 자극 정보는 제시 시작 전에 저장한다.
                logger.write(
                    "digit_trial_start",
                    stage=stage,
                    mode=mode,
                    trial_index=trial_index,
                    stimuli=digits,
                )
                show(win, "+")
                clock = core.Clock()
                start = clock.getTime() + 0.15
                start_ptb = ptb.GetSecs() + 0.15
                for i, digit in enumerate(digits):
                    deadline = start + i * DIGIT_SPAN["digit_interval_s"]
                    target_ptb = start_ptb + i * DIGIT_SPAN["digit_interval_s"]
                    audio[digit].play(when=target_ptb)
                    wait_until(clock, deadline, kb)
                wait_until(
                    clock, start + len(digits) * DIGIT_SPAN["digit_interval_s"], kb
                )
                recalled, rt, key_events = recall_digits(win, kb)
                expected = expected_recall(digits, mode)
                score = score_recall(expected, recalled)
                row = dict(
                    stage=stage,
                    mode=mode,
                    trial_index=trial_index,
                    length=length,
                    stimuli=digits,
                    expected=expected,
                    response=recalled,
                    rt=rt,
                    key_events=key_events,
                    **score,
                )
                logger.write("digit_trial", **row)
                results.append(row)
                failed += not score["exact"]
                if stage == "practice":
                    pause(
                        win,
                        "Correct sequence: "
                        + " ".join(expected)
                        + (
                            "\nCorrect."
                            if score["exact"]
                            else "\nIncorrect. Check the order."
                        ),
                        kb,
                    )
                elif failed >= DIGIT_SPAN["stop_failed_sets"]:
                    break
            logger.write(
                "digit_summary", stage=stage, mode=mode, **span_summary(results)
            )
    finally:
        for item in audio.values():
            item.stop()


if __name__ == "__main__":
    from main import main

    main(default_task="digit_span")
