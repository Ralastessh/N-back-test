"""한 프레임 루프에서 자극·반응·피드백을 처리한다. 키 입력은 시행 시간을 바꾸지 않는다."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import asdict
from statistics import median
from config import (
    NBACK,
    ASSUMPTIONS,
    DISPLAY,
    AUDIO_DIR,
    AUDIO_PLAYBACK,
    NBACK_FEEDBACK,
    NBACK_UI,
    require_decisions,
)
from utils.sequence import generate_block
from utils.scoring import adapt_n, nback_summary
from utils.nback_response import (
    record_response,
    trial_outcomes,
    current_feedback,
    OUTCOME_LABELS,
)


def trial_header(trial, index, n, block):
    progress = f"Warm-up {index + 1}/{n}" if trial.warmup else f"Trial {index - n + 1}/{NBACK['scored_trials']}"
    return f"N={n}  |  Block {block}/{NBACK['blocks']}  |  {progress}"


def run_block(win, kb, shapes, feedback, audio, trials, n, block, logger, frame_s):
    """고정된 프레임 일정. collect_keys와 draw는 대기하거나 다음 시행을 당기지 않는다."""
    visible_frames = round(NBACK["stimulus_s"] / frame_s)
    trial_frames = visible_frames + round(NBACK["isi_s"] / frame_s)
    lead_frames = max(2, round(AUDIO_PLAYBACK["schedule_lead_s"] / frame_s))
    key_map = {NBACK["visual_key"]: "visual", NBACK["auditory_key"]: "auditory"}
    records = [
        dict(
            responses=[],
            feedback_events=[],
            onset=None,
            offset=None,
            complete=False,
            audio_scheduled_ptb=None,
            audio_backend={},
        )
        for _ in trials
    ]
    audio.prepare_block([trial.auditory for trial in trials])
    if hasattr(feedback, "prepare"):
        feedback.prepare([trial_header(trial, i, n, block) for i, trial in enumerate(trials)])
    win.frameIntervals = []
    win.recordFrameIntervals = True

    def collect_keys():
        for key in kb.getKeys(
            keyList=list(key_map) + ["escape"], waitRelease=False, clear=True
        ):
            if key.name == "escape":
                raise KeyboardInterrupt
            accepted = record_response(
                records, key.name, key.rt, key_map, ASSUMPTIONS["response_window_s"]
            )
            if accepted is not None:
                index, modality, first = accepted
                if first:
                    result = trial_outcomes(trials[index], records[index], key_map)[
                        modality
                    ]
                    records[index]["feedback_events"].append(
                        dict(
                            modality=modality,
                            key=key.name,
                            rt=result["rt"],
                            outcome=result["outcome"],
                            text=OUTCOME_LABELS[result["outcome"]],
                            display_onset=None,
                        )
                    )

    try:
        # 음수 프레임: 첫 시청각 자극을 미리 예약하기 위한 준비 구간.
        for frame in range(-lead_frames, len(trials) * trial_frames + 1):
            upcoming_frame = frame + lead_frames
            if upcoming_frame >= 0 and upcoming_frame % trial_frames == 0:
                upcoming = upcoming_frame // trial_frames
                if upcoming < len(trials):
                    when = win.getFutureFlipTime(clock="ptb") + lead_frames * frame_s
                    records[upcoming]["audio_scheduled_ptb"] = when
                    audio.schedule(upcoming, when)
            collect_keys()
            if frame == 0:
                win.callOnFlip(kb.clearEvents)
                win.callOnFlip(kb.clock.reset)
            index, within = divmod(frame, trial_frames)
            if 0 <= index < len(trials):
                trial = trials[index]
                shapes.draw(trial.visual if within < visible_frames else None)
                header = trial_header(trial, index, n, block)
                current = current_feedback(trial, records[index], key_map)
                feedback.draw(header, current if NBACK_FEEDBACK["enabled"] else {})
            else:
                shapes.draw()
            flip_time = win.flip()
            if frame == 0:
                base_flip = flip_time
            if frame >= 0:
                relative_flip = flip_time - base_flip
                if within == 0:
                    if index > 0:
                        records[index - 1]["complete"] = True
                    if index < len(trials):
                        records[index]["onset"] = relative_flip
                if index < len(trials) and within == visible_frames:
                    records[index]["offset"] = relative_flip
                if NBACK_FEEDBACK["enabled"] and index < len(trials):
                    for event in records[index]["feedback_events"]:
                        if event["display_onset"] is None:
                            event["display_onset"] = relative_flip
        # 마지막 시행의 기한 직전 키도 화면 표시 없이 채점에 포함한다.
        collect_keys()
    finally:
        win.recordFrameIntervals = False
        for i, record in enumerate(records):
            if record["onset"] is not None:
                record["audio_backend"] = audio.status(i)
        audio.stop()
        errors = dict(visual=0, auditory=0)
        for trial, record in zip(trials, records):
            if record["onset"] is None:
                continue
            outcomes = trial_outcomes(trial, record, key_map)
            scored = record["complete"] and (
                not trial.warmup or ASSUMPTIONS["score_warmup"]
            )
            for modality, result in outcomes.items():
                if scored and not result["correct"]:
                    errors[modality] += 1
            logger.write(
                "trial",
                block=block,
                n=n,
                **asdict(trial),
                **record,
                stage="test",
                scored=scored,
                outcomes=outcomes,
            )
        logger.write(
            "frame_intervals",
            block=block,
            seconds=list(win.frameIntervals),
            delayed_frames=sum(x > 1.5 * frame_s for x in win.frameIntervals),
        )
    return records, errors


def run(win, logger, seed):
    require_decisions(ASSUMPTIONS, "Dual N-back")
    from stimuli.nback_ui import ParticipantScreens
    from psychopy.hardware import keyboard
    from stimuli.visual import VisualStimuli, FeedbackDisplay
    from stimuli.auditory import AuditoryStimuli

    if NBACK["visual_key"] == NBACK["auditory_key"]:
        raise ValueError("Visual and auditory keys must be different.")
    if not 0 < ASSUMPTIONS["response_window_s"] <= NBACK["stimulus_s"] + NBACK["isi_s"]:
        raise ValueError("The response window must fit inside one trial.")
    win.color = NBACK_UI["background"]
    screens = ParticipantScreens(win)
    kb = keyboard.Keyboard()
    shapes = VisualStimuli(win, DISPLAY)
    feedback = FeedbackDisplay(win)
    audio = AuditoryStimuli(AUDIO_DIR, ASSUMPTIONS["consonants"], NBACK["stimulus_s"])
    screens.welcome(kb)
    audio.check(win, kb, logger, screens=screens)
    screens.instructions(kb)
    flip_times = []
    for _ in range(121):
        win.color = NBACK_UI["flow_background"]
        screens.text("calibration", "Preparing your display...", (0, 0), .032)
        flip_times.append(win.flip())
    calibration = [b - a for a, b in zip(flip_times, flip_times[1:])]
    frame_s = median(calibration)
    if frame_s <= 0:
        raise RuntimeError(
            "Could not measure the display refresh interval. Check VSync."
        )
    win.monitorFramePeriod = frame_s
    win.refreshThreshold = 1.5 * frame_s
    logger.write(
        "timing_setup",
        hz=1 / frame_s,
        calibration_intervals=calibration,
        visible_frames=round(NBACK["stimulus_s"] / frame_s),
        isi_frames=round(NBACK["isi_s"] / frame_s),
        trial_frames=round(NBACK["stimulus_s"] / frame_s)
        + round(NBACK["isi_s"] / frame_s),
        note="Backend/flip timestamps do not verify physical audiovisual onset.",
    )
    n = ASSUMPTIONS["start_n"]
    for block in range(1, NBACK["blocks"] + 1):
        block_seed = seed + block
        trials = generate_block(
            n,
            ASSUMPTIONS["consonants"],
            block_seed,
            **{
                k: NBACK[k]
                for k in (
                    "scored_trials",
                    "visual_targets",
                    "auditory_targets",
                    "simultaneous_targets",
                )
            },
        )
        logger.write(
            "block_start",
            block=block,
            n=n,
            seed=block_seed,
            trials=[asdict(t) for t in trials],
        )
        if block == 1:
            screens.countdown(kb, n, block, frame_s)
        win.color = NBACK_UI["background"]
        records, errors = run_block(
            win, kb, shapes, feedback, audio, trials, n, block, logger, frame_s
        )
        next_n = adapt_n(
            n,
            errors["visual"],
            errors["auditory"],
            min_n=ASSUMPTIONS["min_n"],
            decrease_rule=ASSUMPTIONS["decrease_rule"],
            increase_below=NBACK["increase_below_errors"],
            decrease_above=NBACK["decrease_above_errors"],
        )
        total = sum(record["complete"] and (not trial.warmup or ASSUMPTIONS["score_warmup"])
                    for trial, record in zip(trials, records))
        logger.write("block_summary", block=block, n=n, next_n=next_n, errors=errors,
                     statistics=nback_summary(errors, total))
        if block == NBACK["blocks"]:
            screens.completion(kb, block, n, errors, total=total)
        else:
            rest_elapsed = screens.inter_block_rest(kb, block, n, next_n, errors, total=total)
            logger.write("block_rest", block=block,
                         planned_s=NBACK_UI["inter_block_rest_s"], elapsed_s=rest_elapsed)
        n = next_n
    audio.stop()


if __name__ == "__main__":
    from main import main

    main(default_task="dual_nback")
