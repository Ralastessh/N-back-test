import re
import importlib
import secrets
from config import DATA_DIR, DISPLAY, NBACK_UI, PARTICIPANT_EMAIL_DOMAIN
from utils.data_logger import DataLogger
from utils.native_window import enable_native_fullscreen
from psychopy import visual
from psychopy.hardware import keyboard
from psychopy import prefs
from psychopy import gui

_LOCAL = re.compile(r"[a-z0-9][a-z0-9._%+-]*\Z", re.ASCII)

# 한양대학교 이메일 계정으로 participants 구분 -> data를 CSV로 저장할 때 식별자
def normalize_hanyang_email(value):
    email = str(value or "").strip().lower()
    local, separator, domain = email.partition("@")
    if (not separator or domain != PARTICIPANT_EMAIL_DOMAIN or len(local) > 64 or len(email) > 254 or not _LOCAL.fullmatch(local) or local.endswith(".") or ".." in local):
        raise ValueError(f"Enter your Hanyang University email (@{PARTICIPANT_EMAIL_DOMAIN}).")
    return email

SPAN_TASKS = ("digit_span", "reading_span")
ASSESSMENTS = SPAN_TASKS + ("rapm", "bomat")
TASK_LABELS = {"dual_nback": "Dual N-back", "digit_span": "Digit Span", "reading_span": "Reading Span",
               "rapm": "RAPM examples", "bomat": "BOMAT examples"}

# Pre/Posttest으로 진행
def next_step(task, phase, selected_test):
    if phase == "pretest" and task in ASSESSMENTS:
        return "dual_nback", "training"
    if task == "dual_nback" and phase == "training":
        return selected_test, "posttest"
    return None

def _choice(win, title, choices):
    kb = keyboard.Keyboard()
    # 실험 화면의 기본 UI
    def draw():
        win.color = "#FFFFFF"
        visual.Rect(win, width=3, height=3, fillColor="#FFFFFF", lineColor="#FFFFFF").draw()
        visual.Rect(win, width=3, height=.12, pos=(0, .44), fillColor="#292D32", lineColor="#292D32").draw()
        visual.TextStim(win, text="DUAL-N-BACK STUDY", color="#FFFFFF", height=.035, pos=(0, .44)).draw()
        visual.TextStim(win, text=title, color="#292D32", height=.047, wrapWidth=1.15, pos=(0, .09)).draw()
        width = min(.34, 1.18 / len(choices) - .02)
        for index, label in enumerate(choices.values()):
            x = (index - (len(choices) - 1) / 2) * (width + .02)
            visual.Rect(win, width=width, height=.085, pos=(x, -.23), fillColor="#F3F4F3", lineColor="#DCE0DD").draw()
            visual.TextStim(win, text=label, color="#292D32", height=.020, wrapWidth=width - .01, pos=(x, -.23)).draw()
    # 창 크기 조절 시 다시 draw
    win._resize_draw = draw
    try:
        draw()
        # 다음 화면 갱신 시점에 기존 키 입력 초기화
        win.callOnFlip(kb.clearEvents)
        win.flip()
        # 키값에 해당하는 name 반환(select)
        return kb.waitKeys(keyList=list(choices), waitRelease=False)[0].name
    finally:
        win._resize_draw = None

# 'Pretest -> N-back test -> Posttest' 각 단계 이동 제안
def ask_continue(win, task, phase, next_task, next_phase):
    # 미리 정해진 next task가 없으면 span 선택
    destination = TASK_LABELS[next_task] if next_task else "your chosen test"
    title = (f"{TASK_LABELS[task]} {phase.title()} complete.\n"
             f"Continue to {destination} {next_phase.title()}?")
    return _choice(win, title, {"space": "SPACE  Continue", "n": "N  Finish"}) == "space"

def choose_posttest_task(win):
    while True:
        options = {"d": "digit_span", "r": "reading_span", "a": "rapm", "b": "bomat"}
        labels = {key: f"{key.upper()}  {TASK_LABELS[test]}" for key, test in options.items()}
        key = _choice(win, "Choose the Posttest task.", dict(labels, n="N  Finish"))
        task = options.get(key)
        message = task_phase_error(task, "posttest")
        if message is None:
            return task
        warning = gui.Dlg(title="Check test materials")
        warning.addText(message)
        warning.show()

def task_phase_error(task, phase):
    if task == "dual_nback" and phase != "training":
        return "Dual N-back requires Training. Please choose again."
    if task in ASSESSMENTS and phase not in ("pretest", "posttest"):
        return "Assessment tasks require Pretest or Posttest. Please choose again."
    if task in ("rapm", "bomat"):
        from tasks.matrix_reasoning import load_items
        try:
            load_items(task)
        except (OSError, ValueError, KeyError) as error:
            return str(error)
    return None

def main(default_task=None):
    # sound 모듈을 불러오기 전에 PTB를 선택
    prefs.hardware["audioLib"] = ["ptb", "PTB"]
    tasks = tuple(TASK_LABELS)
    phases = ("training", "pretest", "posttest")
    info = dict(email="", task=default_task or tasks[0], phase=phases[0])
    while True:
        dialog_info = dict(email=info["email"], task=[info["task"]] + [item for item in tasks if item != info["task"]], phase=[info["phase"]] + [item for item in phases if item != info["phase"]])
        if not gui.DlgFromDict(dialog_info, title="Hanyang participant sign-in").OK:
            return
        info = dialog_info
        try:
            email = normalize_hanyang_email(info["email"])
        except ValueError as error:
            message, title = str(error), "Check university email"
        else:
            message = task_phase_error(info["task"], info["phase"])
            title = "Check task, phase and materials"
        if message is None:
            break
        warning = gui.Dlg(title=title)
        warning.addText(message)
        warning.show()
    # 피실험자가 선택한 task, phase, span
    task, phase = info["task"], info["phase"]
    selected_test = task if task in ASSESSMENTS else None
    win = None
    try:
        win = visual.Window(
            size=DISPLAY["size"],
            fullscr=DISPLAY["fullscr"],
            units=DISPLAY["units"], color="#FFFFFF" if task in ASSESSMENTS else DISPLAY["color"], useRetina=DISPLAY["useRetina"],
            allowGUI=True,
            infoMsg="Waiting...",
        )
        enable_native_fullscreen(win)
        while True:
            seed = secrets.randbits(32)
            logger = DataLogger(DATA_DIR, email, task, phase)
            try:
                win.color = NBACK_UI["background"] if task == "dual_nback" else "#FFFFFF"
                # 선택한 task에 맞는 파이썬 파일 불러오기
                module = importlib.import_module("tasks." + ("matrix_reasoning" if task in ("rapm", "bomat") else task))
                module.run(win, logger, seed)
                logger.write("session_end", status="completed")
            except KeyboardInterrupt:
                logger.write("session_end", status="aborted")
                break
            except Exception:
                logger.write("session_end", status="error")
                raise
            finally:
                logger.close()
                print(f"Data saved: {logger.path}")
            following = next_step(task, phase, selected_test)
            if following and following[0] in ("rapm", "bomat"):
                message = task_phase_error(*following)
                if message:
                    warning = gui.Dlg(title="Check Gf materials")
                    warning.addText(message)
                    warning.show()
                    break
            if following is None or not ask_continue(win, task, phase, *following):
                break
            task, phase = following
            if task is None:
                task = choose_posttest_task(win)
                if task is None:
                    break
            if task in ASSESSMENTS:
                selected_test = task
    finally:
        if win is not None:
            win._resize_draw = None
            win.close()

if __name__ == "__main__":
    main()
