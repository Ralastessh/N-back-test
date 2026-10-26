"""PAPER=2008 원문 명시. USER/ASSUMPTION=사용자가 지정·승인한 재현 가정. 단위: 초."""

from pathlib import Path

PROTOCOL_VERSION = "2026-10-26-english-feedback-v2"
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
AUDIO_DIR = ROOT / "stimuli" / "audio"
# PAPER: Materials / Training task
NBACK = dict(
    stimulus_s=0.5,
    isi_s=2.5,
    scored_trials=20,
    blocks=20,
    visual_targets=6,
    auditory_targets=6,
    simultaneous_targets=2,
    visual_key="a",
    auditory_key="l",
    increase_below_errors=3,
    decrease_above_errors=5,
)
# ASSUMPTION: 2026-10-26 사용자 승인. 원문이 구체화하지 않은 조건.
ASSUMPTIONS = dict(
    start_n=2,
    min_n=1,
    decrease_rule="either",
    score_warmup=False,
    response_window_s=3.0,
    consonants=tuple("BFHJMQRW"),
    audio_source="macOS say Samantha English",
)
# USER modification: immediate per-modality feedback, without pausing trials.
NBACK_FEEDBACK = dict(enabled=True, previous_result_s=0.75)
# Use a shared PTB output device. None uses the PsychoPy output preference.
AUDIO_PLAYBACK = dict(
    device_name=None, volume=1.0, check_before_session=True, schedule_lead_s=0.1
)
# 합성 자극 제작 설정. 변경 후 tools/generate_audio.py를 다시 실행한다.
AUDIO_GENERATION = dict(
    voice="Samantha",
    words_per_minute=240,
    sample_rate=48000,
    peak_level=0.7,
    nback_file_s=0.5,
    digit_file_s=0.95,
)
# 기술적 화면 설정 (원문 수치 아님).
DISPLAY = dict(
    size=(1000, 800),
    fullscr=False,
    units="height",
    color="black",
    square_size=0.12,
    spacing=0.22,
    square_color="white",
)
# USER: 원문에 명시되지 않은 사용자 지정 조건. WAIS 원본 복제가 아님.
DIGIT_SPAN = dict(
    forward_lengths=list(range(3, 10)),
    backward_lengths=list(range(2, 9)),
    trials_per_length=2,
    digit_pool=list("123456789"),
    adjacent_repetitions=False,
    digit_interval_s=1.0,
    stop_failed_sets=2,
    presentation="auditory",
    practice_trials=2,
    audio_subdir="digits",
    audio_source="macOS say Samantha English",
)
# USER: 사용자 지정 Reading Span. 승인되지 않은 문항은 실행 불가.
READING_SPAN = dict(
    lengths=[2, 3, 4, 5],
    sets_per_size=3,
    randomized_set_order=True,
    timeout_sd_multiplier=2.5,
    processing_flag_below=0.85,
    practice_sets=3,
    practice_set_size=2,
    min_correct_practice_rts=2,
    form_by_phase={"pretest": "A", "posttest": "B"},
    sentence_file="stimuli/reading_sentences.csv",
    review_file="stimuli/reading_review.json",
    true_key="y",
    false_key="n",
    early_stopping=False,
)


def require_decisions(settings, label):
    missing = [k for k, v in settings.items() if v is None]
    if missing:
        raise ValueError(
            f"{label}: researcher settings required: " + ", ".join(missing)
        )
