from config import DIGIT_SPAN, AUDIO_DIR
from psychopy import core
import random
from utils.scoring import score_recall

# 최대한 중복이 없는 상황을 연출하여 같은 숫자를 그대로 반복해서 기억하는 효과를 줄임
def digit_plans(seed, settings):
    # 실험의 재현성 확보를 위해 난수 생성기 사용
    rng = random.Random(f"digit:{seed}")
    pool = [str(d) for d in settings["digit_pool"]]
    # 길이 n 숫자열을 각각 몇 번씩 수행할지에 대한 length
    lengths = [n for n in settings["lengths"] for _ in range(settings["trials_per_length"])]
    used, plans = set(), {}
    for phase in ("pretest", "posttest"):
        sequences = []
        for length in lengths:
            for _ in range(10000):
                digits = []
                for _ in range(length):
                    # 숫자 중복 등의 조건들을 만족하는 숫자열 후보군을 저장
                    candidates = [d for d in pool if settings["adjacent_repetitions"]
                                  or not digits or d != digits[-1]]
                    if not candidates:
                        raise ValueError("No eligible digit candidates.")
                    digits.append(rng.choice(candidates))
                key = tuple(digits)
                # 이미 사용된 숫자열은 스킵
                if key not in used:
                    break
            else:
                raise ValueError("Cannot generate unique sequences with these settings.")
            used.add(key)
            sequences.append(digits)
        # 실제 실험에 사용할 숫자열을 plans에 저장
        rng.shuffle(sequences)
        plans[phase] = sequences
    return plans

# 숫자 음성 재생 간격을 일정하게 유지하기 위한 대기 함수
def wait_until(clock, deadline, kb):
    while clock.getTime() < deadline:
        # 실험 도중 ESC를 누르면 중단
        if kb.getKeys(keyList=["escape"], waitRelease=False):
            raise KeyboardInterrupt
        # CPU의 불필요한 점유를 줄이기 위해 짧은 간격으로 대기
        core.wait(0.001)

# 실험 진행 단계에 따라 준비, 청취, 회상 화면을 구분하여 표시
def draw_screen(screens, state, response=(), progress=""):
    theme = screens.theme
    ink, muted, accent = theme["flow_text"], theme["flow_muted"], theme["flow_accent"]
    screens.win.color = "#FFFFFF"
    screens.panel("digit_background", (0, 0), (3, 1), "#FFFFFF")
    screens.text("digit_title", "Digit Span", (0, .385), .048, ink)
    screens.panel("digit_rule", (0, .31), (1.12, .002), theme["flow_border"])
    if progress:
        screens.text("digit_progress", progress, (0, .255), .021, muted)

    # 실험 시작 전 안내 화면
    if state == "ready":
        screens.text("digit_intro", "Listen. Remember. Recall.", (0, .13), .043, ink)
        screens.text("digit_intro_note", "Listen to the numbers, then type them in the same order.",
                     (0, .035), .027, muted, 1.0)
        screens.panel("digit_intro_card", (0, -.11), (1.08, .13), theme["flow_panel"])
        screens.text("digit_intro_tip", f"{len(DIGIT_SPAN['lengths']) * DIGIT_SPAN['trials_per_length']} sequences. Wait until the sound ends before typing.",
                     (0, -.11), .024, ink)
        screens.panel("digit_begin", (0, -.29), (.46, .075), accent)
        screens.text("digit_begin_text", "SPACE   Begin", (0, -.29), .025, "white")

    # 숫자를 듣는 동안에는 고정점만 표시하여 시각적 방해를 최소화
    elif state == "listening":
        screens.text("digit_listening", "Listening", (0, .13), .035, ink)
        screens.panel("digit_focus_card", (0, -.015), (1.08, .20), theme["flow_panel"])
        screens.text("digit_fixation", "+", (0, -.015), .070, accent)
        screens.text("digit_listening_note", "Keep the numbers in mind.", (0, -.19), .025, muted)

    # 음성 재생이 끝난 뒤 기억한 숫자를 입력하는 화면
    else:
        screens.text("digit_recall_note", "Type the numbers in the same order.", (0, .18), .027, muted)
        screens.panel("digit_input", (0, .015), (1.08, .23), theme["flow_panel"], accent)
        screens.text("digit_response", " ".join(response) if response else "Enter numbers",
                     (0, .015), .065 if response else .032, ink if response else muted, 1.0)
        for x, key, label in ((-.29, "BACKSPACE", "Edit"), (.29, "ENTER", "Submit")):
            fill = accent if key == "ENTER" else theme["flow_panel"]
            screens.panel("digit_" + key, (x, -.27), (.52, .075), fill)
            screens.text("digit_" + key + "_text", f"{key}   {label}", (x, -.27), .022,
                         "white" if key == "ENTER" else ink, .50)
    screens.text("digit_exit", "ESC   Exit", (0, -.435), .019, muted)

# 참가자가 기억한 숫자를 입력받고 입력 순서 및 반응시간 기록
def recall_digits(win, kb, screens, progress):
    response = []
    events = []

    def draw():
        draw_screen(screens, "recall", response, progress)

    # 창 크기가 변경될 경우 현재 입력 상태를 다시 표시하기 위한 함수 등록
    win._resize_draw = draw

    # Recall 화면이 실제 표시되는 시점에 기존 키 기록과 RT 시계를 초기화
    win.callOnFlip(kb.clearEvents)
    win.callOnFlip(kb.clock.reset)
    draw()
    win.flip()

    try:
        while True:
            # 키 입력을 계속 확인하되 입력이 없어도 프로그램이 멈추지 않도록 함
            for key in kb.getKeys(waitRelease=False, clear=True):
                # 숫자 입력뿐 아니라 수정 및 제출 기록까지 저장
                events.append(dict(key=key.name, rt=key.rt))

                if key.name == "escape":
                    raise KeyboardInterrupt

                # Enter를 누르면 입력을 확정하고 응답, 제출시간, 키 기록 반환
                if key.name in ("return", "num_enter"):
                    return response, key.rt, events

                if key.name == "backspace":
                    response = response[:-1]
                elif key.name in DIGIT_SPAN["digit_pool"]:
                    response.append(key.name)

                # 참가자가 입력한 숫자를 화면에 실시간으로 반영
                draw()
                win.flip()
            core.wait(0.001)
    finally:
        win._resize_draw = None

# Digit Span 실험 전체 실행
def run(win, logger, seed):
    from psychopy import sound
    import psychtoolbox as ptb
    from psychopy.hardware import keyboard
    from stimuli.nback_ui import ParticipantScreens

    win.color = "#FFFFFF"
    kb = keyboard.Keyboard()
    screens = ParticipantScreens(win)

    # 동일한 seed를 사용하면 같은 숫자열을 생성할 수 있도록 설정
    plans = digit_plans(seed, DIGIT_SPAN)

    # 숫자 음성을 미리 로딩하여 재생 시 발생할 수 있는 지연을 줄임
    audio = {
        d: sound.Sound(
            str(AUDIO_DIR / DIGIT_SPAN["audio_subdir"] / f"{d}.wav"), preBuffer=-1
        )
        for d in DIGIT_SPAN["digit_pool"]
    }

    # 숫자 음성이 다음 숫자의 제시 시점까지 이어지지 않도록 길이 확인
    if any(s.getDuration() > DIGIT_SPAN["digit_interval_s"] for s in audio.values()):
        raise ValueError("A digit recording is longer than the presentation interval.")

    try:
        screens.wait(kb, draw_screen, screens, "ready")

        # Pretest와 Posttest에서 서로 다른 숫자열 사용
        sequences = plans[logger.phase]

        for trial_index, digits in enumerate(sequences):
            length = len(digits)

            # 실제 제시할 숫자열을 미리 기록하여 중단된 시행도 추적 가능하게 함
            trial_info = dict(stage="test", mode="forward", random_seed=seed,
                              trial_index=trial_index, stimuli=digits)
            logger.write("digit_trial_start", **trial_info)
            
            progress = f"Sequence {trial_index + 1} / {len(sequences)}"

            # 숫자 재생 중에는 청취 화면을 유지
            win._resize_draw = lambda: draw_screen(screens, "listening", progress=progress)
            win._resize_draw()
            win.flip()

            # PsychoPy와 PTB의 시간 기준을 이용해 숫자별 재생 시점 계산
            clock = core.Clock()
            start = clock.getTime() + 0.15
            start_ptb = ptb.GetSecs() + 0.15

            for i, digit in enumerate(digits):
                deadline = start + i * DIGIT_SPAN["digit_interval_s"]
                target_ptb = start_ptb + i * DIGIT_SPAN["digit_interval_s"]
                # PTB를 통해 숫자 음성을 일정한 시간 간격으로 재생 예약
                audio[digit].play(when=target_ptb)
                wait_until(clock, deadline, kb)

            # 마지막 숫자까지 제시 간격을 유지한 뒤 회상 단계로 이동
            wait_until(clock, start + len(digits) * DIGIT_SPAN["digit_interval_s"], kb)
            # 참가자의 회상 결과와 키 입력 기록 수집
            recalled, rt, key_events = recall_digits(win, kb, screens, progress)
            # 제시한 숫자열과 참가자의 응답을 비교하여 정확도 계산
            score = score_recall(digits, recalled)

            # 숫자 길이, 정답, 응답, RT, 정확도를 모두 기록
            logger.write("digit_trial", **trial_info, length=length, expected=digits, response=recalled, rt=rt, key_events=key_events, **score)
    finally:
        # 실험이 중단되더라도 화면 설정과 오디오를 정리
        win._resize_draw = None
        for item in audio.values():
            item.stop()
