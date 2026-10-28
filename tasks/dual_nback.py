import sys
from pathlib import Path
from dataclasses import asdict
from statistics import median

from psychopy.hardware import keyboard
from stimuli.nback_ui import ParticipantScreens
from stimuli.visual import VisualStimuli, FeedbackDisplay
from stimuli.auditory import AuditoryStimuli
from config import (
    NBACK,
    ASSUMPTIONS,
    DISPLAY,
    AUDIO_DIR,
    AUDIO_PLAYBACK,
    NBACK_FEEDBACK,
    NBACK_UI,
)
from utils.sequence import generate_block
from utils.scoring import (
    adapt_n, nback_summary,
    record_response,
    trial_outcomes,
    current_feedback,
)

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# 현재 블록, N-back 난이도, Trial 진행 상황을 화면에 표시하기 위한 문구 생성
def trial_header(trial, index, n, block):
    progress = f"Warm-up {index + 1}/{n}" if trial.warmup else f"Trial {index - n + 1}/{NBACK['scored_trials']}"
    return f"N={n}  |  Block {block}/{NBACK['blocks']}  |  {progress}"


# 한 블록의 시청각 자극 제시, 키 입력, 정답 판정 및 데이터 기록
def run_block(win, kb, shapes, feedback, audio, trials, n, block, logger, frame_s):
    # 모니터의 프레임 주기를 기준으로 자극 제시 시간과 ISI를 프레임 수로 변환
    visible_frames = round(NBACK["stimulus_s"] / frame_s)
    trial_frames = visible_frames + round(NBACK["isi_s"] / frame_s)

    # 시각 자극과 청각 자극의 동기화를 위해 오디오 재생을 미리 예약할 프레임 수
    lead_frames = max(2, round(AUDIO_PLAYBACK["schedule_lead_s"] / frame_s))
    key_map = {NBACK["visual_key"]: "visual", NBACK["auditory_key"]: "auditory"}

    # 각 Trial의 반응, 실제 자극 시작 및 종료 시각 등을 독립적으로 저장
    records = [
        dict(
            responses=[],
            onset=None,
            offset=None,
            complete=False,
        )
        for _ in trials
    ]

    # 실험 도중 파일 로딩이나 글자 생성으로 프레임이 지연되지 않도록 사전 준비
    audio.prepare_block([trial.auditory for trial in trials])
    feedback.prepare([trial_header(trial, i, n, block) for i, trial in enumerate(trials)])

    def collect_keys():
        # 키 입력을 기다리느라 Trial 진행 시간이 늘어나지 않도록 비차단 방식으로 수집
        for key in kb.getKeys(
            keyList=list(key_map) + ["escape"], waitRelease=False, clear=True
        ):
            if key.name == "escape":
                raise KeyboardInterrupt

            # 시각과 청각 반응을 구분하여 해당 Trial의 입력 기록에 저장
            record_response(
                records, key.name, key.rt, key_map, ASSUMPTIONS["response_window_s"]
            )

    try:
        # 첫 자극보다 앞선 준비 프레임부터 시작하여 오디오 재생 시점을 미리 예약
        for frame in range(-lead_frames, len(trials) * trial_frames + 1):
            upcoming_frame = frame + lead_frames

            # 다음 Trial 시작 시점에 맞춰 청각 자극의 재생을 예약
            if upcoming_frame >= 0 and upcoming_frame % trial_frames == 0:
                upcoming = upcoming_frame // trial_frames
                if upcoming < len(trials):
                    when = win.getFutureFlipTime(clock="ptb") + lead_frames * frame_s
                    audio.schedule(upcoming, when)

            # 자극 제시와 관계없이 매 프레임마다 키 입력 확인
            collect_keys()

            # 첫 번째 Trial이 화면에 표시되는 시점부터 반응시간 측정
            if frame == 0:
                win.callOnFlip(kb.clearEvents)
                win.callOnFlip(kb.clock.reset)

            # 현재 프레임이 몇 번째 Trial의 어느 시점에 해당하는지 계산
            index, within = divmod(frame, trial_frames)

            if 0 <= index < len(trials):
                trial = trials[index]

                # 처음 500ms 동안만 사각형을 표시하고 나머지 ISI에서는 제거
                shapes.draw(trial.visual if within < visible_frames else None)

                header = trial_header(trial, index, n, block)
                current = current_feedback(trial, records[index], key_map)

                # 피드백 설정에 따라 현재 반응 결과 표시 여부 결정
                feedback.draw(header, current if NBACK_FEEDBACK["enabled"] else {})
            else:
                shapes.draw()

            # win.flip()을 기준으로 일정한 프레임 간격을 유지하면서 화면 갱신
            flip_time = win.flip()

            if frame == 0:
                base_flip = flip_time

            if frame >= 0:
                # 실제 화면 갱신 시각을 첫 Trial 시작 시점에 대한 상대시간으로 기록
                relative_flip = flip_time - base_flip

                if within == 0:
                    if index > 0:
                        records[index - 1]["complete"] = True
                    if index < len(trials):
                        records[index]["onset"] = relative_flip

                if index < len(trials) and within == visible_frames:
                    records[index]["offset"] = relative_flip

        # 마지막 Trial이 종료되기 직전까지의 키 입력도 반응 기록에 포함
        collect_keys()

    finally:
        audio.stop()
        errors = dict(visual=0, auditory=0)

        for trial, record in zip(trials, records):
            # 실제로 제시되지 않은 Trial은 채점에서 제외
            if record["onset"] is None:
                continue

            # 시각과 청각의 Hit, Miss, False Alarm 등을 독립적으로 판정
            outcomes = trial_outcomes(trial, record, key_map)

            # 완료된 Trial만 채점하며 초기 n개의 Warm-up은 설정에 따라 제외
            scored = record["complete"] and (
                not trial.warmup or ASSUMPTIONS["score_warmup"]
            )

            for modality, result in outcomes.items():
                if scored and not result["correct"]:
                    errors[modality] += 1

            # 자극 정보, 반응시간, 정답 여부 및 실제 제시 시각을 Trial별로 저장
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

    return records, errors


# Dual N-back의 전체 세션을 실행하고 블록별 난이도를 조절
def run(win, logger, seed):
    # 시각과 청각 반응에 같은 키를 사용하는 상황 방지
    if NBACK["visual_key"] == NBACK["auditory_key"]:
        raise ValueError("Visual and auditory keys must be different.")

    # 반응 허용 시간이 하나의 Trial을 초과하지 않도록 검사
    if not 0 < ASSUMPTIONS["response_window_s"] <= NBACK["stimulus_s"] + NBACK["isi_s"]:
        raise ValueError("The response window must fit inside one trial.")

    win.color = NBACK_UI["background"]
    screens = ParticipantScreens(win)
    kb = keyboard.Keyboard()

    # 시각 자극, 피드백, 청각 자극을 각각 별도의 객체로 관리
    shapes = VisualStimuli(win, DISPLAY)
    feedback = FeedbackDisplay(win)
    audio = AuditoryStimuli(AUDIO_DIR, ASSUMPTIONS["consonants"], NBACK["stimulus_s"])

    screens.welcome(kb)
    audio.check(win, kb, screens)
    screens.instructions(kb)

    # 실제 모니터의 화면 갱신 간격을 측정하여 자극 제시 시간을 프레임 단위로 설정
    flip_times = []
    for _ in range(121):
        win.color = NBACK_UI["flow_background"]
        screens.text("calibration", "Preparing your display...", (0, 0), .032)
        flip_times.append(win.flip())

    # 측정한 프레임 간격의 중앙값을 사용하여 일시적인 지연의 영향 감소
    frame_s = median(b - a for a, b in zip(flip_times, flip_times[1:]))

    if frame_s <= 0:
        raise RuntimeError(
            "Could not measure the display refresh interval. Check VSync."
        )

    win.monitorFramePeriod = frame_s

    # 설정된 초기 N-back 수준에서 시작
    n = ASSUMPTIONS["start_n"]

    for block in range(1, NBACK["blocks"] + 1):
        # 각 블록마다 Target 개수를 유지하면서 새로운 시청각 자극 시퀀스 생성
        trials = generate_block(
            n, ASSUMPTIONS["consonants"], seed + block,
            scored_trials=NBACK["scored_trials"],
            visual_targets=NBACK["visual_targets"],
            auditory_targets=NBACK["auditory_targets"],
            simultaneous_targets=NBACK["simultaneous_targets"],
        )

        if block == 1:
            screens.countdown(kb, n, block, frame_s)

        win.color = NBACK_UI["background"]

        # 한 블록의 모든 Trial을 실행하고 시각/청각 오류 수를 각각 계산
        records, errors = run_block(
            win, kb, shapes, feedback, audio, trials, n, block, logger, frame_s
        )

        # 블록의 수행 결과에 따라 다음 블록의 N-back 수준을 조절
        next_n = adapt_n(
            n,
            errors["visual"],
            errors["auditory"],
            min_n=ASSUMPTIONS["min_n"],
            decrease_rule=ASSUMPTIONS["decrease_rule"],
            increase_below=NBACK["increase_below_errors"],
            decrease_above=NBACK["decrease_above_errors"],
        )

        # 초기 Warm-up을 제외하고 실제 채점에 포함된 Trial 수 계산
        total = sum(record["complete"] and (not trial.warmup or ASSUMPTIONS["score_warmup"])
                    for trial, record in zip(trials, records))

        # 블록별 오류 수와 다음 난이도를 기록하여 훈련에 따른 수행 변화 확인
        logger.write("block_summary", block=block, next_n=next_n,
                     statistics=nback_summary(errors, total))

        # 마지막 블록이면 종료 화면, 그 외에는 다음 블록 전 안내 화면 표시
        if block == NBACK["blocks"]:
            screens.completion(kb, block, n, errors, total=total)
        else:
            screens.inter_block_rest(kb, block, n, next_n, errors, total=total)

        n = next_n


# 이 파일을 직접 실행하면 Dual N-back을 기본 과제로 설정
if __name__ == "__main__":
    from main import main

    main(default_task="dual_nback")
