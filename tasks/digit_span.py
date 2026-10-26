"""사용자 지정 청각 숫자 폭 검사. WAIS 원본 검사가 아니다."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DIGIT_SPAN, AUDIO_DIR
from utils.span_protocol import digit_plans, expected_recall, span_summary
from utils.scoring import score_recall
from utils.span_ui import show, pause, wait_until, recall_digits


def run(win, logger, seed, mode="forward"):
    from psychopy import core, sound
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
                import psychtoolbox as ptb

                start_ptb = ptb.GetSecs() + 0.15
                actual = []
                for i, digit in enumerate(digits):
                    deadline = start + i * DIGIT_SPAN["digit_interval_s"]
                    target_ptb = start_ptb + i * DIGIT_SPAN["digit_interval_s"]
                    audio[digit].play(when=target_ptb)
                    wait_until(clock, deadline, kb)
                    actual.append(
                        dict(
                            digit=digit,
                            scheduled_ptb=target_ptb,
                            dispatch_clock=clock.getTime(),
                        )
                    )
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
                    audio_schedule=actual,
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
                    logger.write(
                        "digit_discontinue",
                        stage=stage,
                        mode=mode,
                        length=length,
                        failures=failed,
                    )
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
