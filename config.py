from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PARTICIPANT_EMAIL_DOMAIN = "hanyang.ac.kr"
AUDIO_DIR = ROOT / "stimuli" / "audio"
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

ASSUMPTIONS = dict(
    start_n=2,
    min_n=1,
    decrease_rule="either",
    score_warmup=False,
    response_window_s=3.0,
    consonants=tuple("BFHJMQRW"),
)
NBACK_FEEDBACK = dict(enabled=True)
AUDIO_PLAYBACK = dict(
    device_name=None, volume=1.0, check_before_session=True, schedule_lead_s=0.1
)
DISPLAY = dict(
    size=(1000, 800),
    fullscr=False,
    useRetina=True,
    units="height",
    color="black",
    square_size=0.12,
    spacing=0.22,
    square_color="#65AEFF",
)
NBACK_UI = dict(
    background="#0D1522",
    panel="#18263A",
    border="#2C405B",
    text="#EDF4FF",
    muted="#ACBDD3",
    correct="#7EE0B8",
    incorrect="#FFB89E",
    feedback_height=0.044,
    feedback_y=-0.405,
    feedback_panel_height=0.14,
    font_path="/System/Library/Fonts/Helvetica.ttc",  # macOS TrueType, 네이티브 픽셀 렌더링
    countdown_s=3,
    inter_block_rest_s=10,
    flow_background="#FFFFFF",
    flow_header="#292D32",
    flow_panel="#F3F4F3",
    flow_border="#DCE0DD",
    flow_text="#292D32",
    flow_muted="#626B67",
    flow_accent="#487763",
)
DIGIT_SPAN = dict(
    lengths=list(range(3, 10)),
    trials_per_length=2,
    digit_pool=list("123456789"),
    adjacent_repetitions=False,
    digit_interval_s=1.0,
    stop_failed_sets=2,
    audio_subdir="digits",
)
READING_SPAN = dict(
    lengths=[2, 3, 4, 5],
    sets_per_size=3,
    randomized_set_order=True,
    sentence_timeout_s=5.0,
    form_by_phase={"pretest": "A", "posttest": "B"},
    sentence_file="stimuli/reading_sentences.csv",
    true_key="y",
    false_key="n",
)
