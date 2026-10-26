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
    require_decisions,
)
from utils.sequence import generate_block
from utils.scoring import adapt_n
from utils.nback_response import (
    record_response,
    trial_outcomes,
    current_feedback,
    completed_feedback,
    OUTCOME_LABELS,
)


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
            result_display_onset=None,
            audio_scheduled_ptb=None,
            audio_backend={},
        )
        for _ in trials
    ]
    audio.prepare_block([trial.auditory for trial in trials])
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
            shown_records = []
            if 0 <= index < len(trials):
                trial = trials[index]
                shapes.draw(trial.visual if within < visible_frames else None)
                header = (
                    f"{n}-back | Warm-up {index + 1}/{n} (not scored)"
                    if trial.warmup
                    else f'{n}-back | Trial {index - n + 1}/{NBACK["scored_trials"]}'
                )
                current = current_feedback(trial, records[index], key_map)
                previous = ""
                # 경계 flip 이후에 키 큐를 다시 읽은 다음, 이전 시행의 무응답을 판정한다.
                if (
                    index > 0
                    and 0 < within * frame_s <= NBACK_FEEDBACK["previous_result_s"]
                ):
                    previous = "Previous trial: " + completed_feedback(
                        trials[index - 1], records[index - 1], key_map
                    )
                    shown_records.append(index - 1)
                if NBACK_FEEDBACK["enabled"]:
                    feedback.draw(header, current, previous)
                    shown_records.append(index)
                else:
                    feedback.draw(header, {})
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
                if NBACK_FEEDBACK["enabled"]:
                    for shown in shown_records:
                        for event in records[shown]["feedback_events"]:
                            if event["display_onset"] is None:
                                event["display_onset"] = relative_flip
                        if (
                            shown < index
                            and records[shown]["result_display_onset"] is None
                        ):
                            records[shown]["result_display_onset"] = relative_flip
        # 최종 응답 구간의 마지막 프레임에 들어온 키도 발생 시각에 따라 수집한다.
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
    from psychopy import visual
    from psychopy.hardware import keyboard
    from stimuli.visual import VisualStimuli, FeedbackDisplay
    from stimuli.auditory import AuditoryStimuli

    if NBACK["visual_key"] == NBACK["auditory_key"]:
        raise ValueError("Visual and auditory keys must be different.")
    if not 0 < ASSUMPTIONS["response_window_s"] <= NBACK["stimulus_s"] + NBACK["isi_s"]:
        raise ValueError("The response window must fit inside one trial.")
    kb = keyboard.Keyboard()
    shapes = VisualStimuli(win, DISPLAY)
    feedback = FeedbackDisplay(win)
    audio = AuditoryStimuli(AUDIO_DIR, ASSUMPTIONS["consonants"], NBACK["stimulus_s"])
    audio.check(win, kb, logger)
    flip_times = [win.flip() for _ in range(121)]
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
    message = visual.TextStim(
        win,
        height=0.029,
        wrapWidth=1.15,
        text=(
            f'Press {NBACK["visual_key"].upper()} only when the LOCATION matches N trials back.\n'
            f'Press {NBACK["auditory_key"].upper()} only when the spoken LETTER matches N trials back.\n'
            "If BOTH match, press BOTH keys. If neither matches, press nothing.\n\n"
            f'Respond any time within {ASSUMPTIONS["response_window_s"]:g} seconds of onset.\n'
            "Correct / Incorrect feedback appears when you press a response key.\n"
            "The next trial starts on schedule, regardless of your response.\n"
            "The first N presentations are memory warm-up trials.\n\nSPACE: start | ESC: quit"
        ),
    )
    message.draw()
    win.flip()
    if any(
        k.name == "escape"
        for k in kb.waitKeys(keyList=["space", "escape"], waitRelease=False)
    ):
        raise KeyboardInterrupt
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
        logger.write("block_summary", block=block, n=n, next_n=next_n, errors=errors)
        key_map = {NBACK["visual_key"]: "visual", NBACK["auditory_key"]: "auditory"}
        final_result = completed_feedback(trials[-1], records[-1], key_map)
        message.text = (
            f'Block {block}/{NBACK["blocks"]} complete\n'
            f'Visual errors: {errors["visual"]} | Auditory errors: {errors["auditory"]}\n'
            f"Last trial:\n{final_result}\n\nNext N: {next_n}\nSPACE: continue | ESC: quit"
        )
        message.draw()
        win.flip()
        if any(
            k.name == "escape"
            for k in kb.waitKeys(keyList=["space", "escape"], waitRelease=False)
        ):
            raise KeyboardInterrupt
        n = next_n
    audio.stop()


if __name__ == "__main__":
    from main import main

    main(default_task="dual_nback")
