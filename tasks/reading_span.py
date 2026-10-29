from pathlib import Path
import csv
import random
from config import ROOT, READING_SPAN
from utils.scoring import score_recall
from psychopy import visual
from psychopy.hardware import keyboard
from stimuli.nback_ui import ParticipantScreens

# CSV에서 문장을 불러오고 실험 조건에 맞게 구성되었는지 확인
def load_reading_materials(path, settings):
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as f:
        # P는 연습 문항이므로 실제 사전/사후검사에서는 제외
        rows = [row for row in csv.DictReader(f) if row["form"] != "P"]

    groups = {form: {} for form in ("A", "B")}
    ids = set()

    for row in rows:
        form = row["form"]
        if form not in groups:
            raise ValueError("Form must be A or B.")

        # 각 문항의 ID가 중복되지 않도록 검사
        if not row["item_id"] or row["item_id"] in ids:
            raise ValueError("Duplicate or missing item_id.")
        ids.add(row["item_id"])

        if row["answer"] not in ("True", "False"):
            raise ValueError("Answer must be True or False.")

        row["truth"] = row["answer"] == "True"

        if not row["sentence"].strip() or not row["recall_word"].strip():
            raise ValueError("Empty sentence or recall word.")

        # 설정된 단어 수와 실제 문장의 단어 수가 일치하는지 확인
        if int(row["word_count"]) != len(row["sentence"].split()):
            raise ValueError(f'{row["item_id"]}: update word_count.')

        # 회상해야 하는 단어가 실제 문장의 마지막 단어인지 확인
        final = row["sentence"].strip().split()[-1].rstrip(".!?。")
        if final != row["recall_word"]:
            raise ValueError(f'{row["item_id"]}: recall_word does not match the final word.')

        # Form별로 문장들을 각 Set에 배정
        groups[form].setdefault(row["set_id"], []).append(row)

    # Set Size별 시행 횟수가 설정값과 일치하는지 확인
    expected = [n for n in settings["lengths"] for _ in range(settings["sets_per_size"])]

    for form, sets in groups.items():
        if sorted(map(len, sets.values())) != sorted(expected):
            raise ValueError(f"{form}: invalid set composition.")

        truths = []
        for group in sets.values():
            # 문장이 CSV에 지정된 순서대로 제시되도록 정렬
            group.sort(key=lambda r: int(r["item_order"]))

            if [int(r["item_order"]) for r in group] != list(range(1, len(group) + 1)):
                raise ValueError("Invalid item_order.")

            if any(int(r["set_size"]) != len(group) for r in group):
                raise ValueError("Invalid set_size.")

            truths.extend(r["truth"] for r in group)

        # True와 False 문항의 수를 동일하게 유지
        if sum(truths) * 2 != len(truths):
            raise ValueError(f"{form}: True/False counts are not balanced.")

    # Pre/Post 문항의 Set Size, 순서, 정답 구성이 대응되도록 검사
    a = {r["pair_id"]: r for r in rows if r["form"] == "A"}
    b = {r["pair_id"]: r for r in rows if r["form"] == "B"}

    if (len(a) != sum(map(len, groups["A"].values())) or len(b) != sum(map(len, groups["B"].values())) or set(a) != set(b)):
        raise ValueError("A/B pair_id mismatch or duplicate.")

    for key in a:
        if any(a[key][k] != b[key][k] for k in ("set_size", "item_order", "answer")):
            raise ValueError("A/B paired item structure does not match.")

    return groups

# 실험 단계에 따라 안내, 문장 판단, 단어 회상 화면을 표시
def draw_screen(screens, state, progress="", sentence="", entry=None):
    theme = screens.theme
    ink, muted, accent = theme["flow_text"], theme["flow_muted"], theme["flow_accent"]

    screens.win.color = "#FFFFFF"
    screens.panel("reading_background", (0, 0), (3, 1), "#FFFFFF")
    screens.text("reading_title", "Reading Span", (0, .385), .048, ink)
    screens.panel("reading_rule", (0, .31), (1.12, .002), theme["flow_border"])
    screens.text("reading_progress", progress, (0, .255), .021, muted)

    # 실험 시작 전 문장 판단과 단어 회상 방법 안내
    if state == "ready":
        screens.text("reading_intro", "Read. Decide. Remember.", (0, .15), .043, ink)
        screens.text("reading_note", "Decide whether each sentence makes sense.\nRemember the final words in order.",
                     (0, .04), .027, muted, 1.05)
        screens.panel("reading_tip_card", (0, -.12), (1.08, .14), theme["flow_panel"])
        screens.text("reading_tip", f"{len(READING_SPAN['lengths']) * READING_SPAN['sets_per_size']} sets. {READING_SPAN['sentence_timeout_s']:g} seconds per sentence.\nThen type the final words in the same order.",
                     (0, -.12), .025, ink, 1.0)
        screens.panel("reading_begin", (0, -.29), (.46, .075), accent)
        screens.text("reading_begin_text", "SPACE   Begin", (0, -.29), .025, "white")

    # 문장을 읽고 제한 시간 내에 True/False를 판단하는 단계
    elif state == "judgment":
        screens.panel("reading_sentence_card", (0, .035), (1.12, .34), theme["flow_panel"])
        screens.text("reading_sentence", sentence, (0, .035), .034, ink, 1.0)
        screens.text("reading_limit", f"{READING_SPAN['sentence_timeout_s']:g} seconds to decide", (0, -.19), .023, muted)

        for x, key, label in ((-.29, READING_SPAN["true_key"], "True"),
                               (.29, READING_SPAN["false_key"], "False")):
            screens.panel("reading_" + label, (x, -.29), (.52, .075), theme["flow_panel"], accent)
            screens.text("reading_" + label + "_text", f"{key.upper()}   {label}", (x, -.29), .025, ink)

    # 하나의 Set이 끝나면 각 문장의 마지막 단어를 순서대로 회상
    else:
        screens.text("reading_recall_note", "Type the final words in the same order.", (0, .18), .027, muted)
        screens.panel("reading_input", (0, .015), (1.08, .23), theme["flow_panel"], accent)
        entry.draw()
        screens.text("reading_recall_tip", "Separate words with spaces. Use _ for a missing word.",
                     (0, -.17), .023, muted, 1.1)
        screens.panel("reading_submit", (0, -.29), (.46, .075), accent)
        screens.text("reading_submit_text", "ENTER   Submit", (0, -.29), .025, "white")

    screens.text("reading_exit", "ESC   Exit", (0, -.435), .019, muted)


# 한 Set에서 기억한 마지막 단어들을 입력받는 함수
def recall_words(win, kb, screens, progress):
    # TextBox2를 사용하여 참가자가 키보드로 단어를 직접 입력할 수 있게 함
    entry = visual.TextBox2(
        win, text="", font="Helvetica", units="height", pos=(0, .015), size=(1.0, .20),
        letterHeight=.034, padding=.015, color=screens.theme["flow_text"],
        alignment="left", editable=True, placeholder="Enter words", autoLog=False,
    )
    entry.hasFocus = True

    def draw():
        draw_screen(screens, "recall", progress, entry=entry)

    win._resize_draw = draw

    # 회상 화면이 표시되는 시점부터 RT를 측정하기 위해 키 기록과 시계 초기화
    win.callOnFlip(kb.clearEvents)
    win.callOnFlip(kb.clock.reset)

    try:
        draw()
        win.flip()

        while True:
            # Enter로 입력을 제출하고 ESC로 실험 중단
            for key in kb.getKeys(keyList=["return", "num_enter", "escape"], waitRelease=False, clear=True):
                if key.name == "escape":
                    raise KeyboardInterrupt
                # 공백을 기준으로 단어를 분리하여 회상 순서와 제출시간 반환
                return entry.text.strip().split(), key.rt
            draw()
            win.flip()
    finally:
        entry.editable = False
        win._resize_draw = None

# Reading Span 실험 전체 실행
def run(win, logger, seed):
    kb = keyboard.Keyboard()
    screens = ParticipantScreens(win)
    settings = READING_SPAN
    timeout = settings["sentence_timeout_s"]

    if timeout <= 0:
        raise ValueError("Sentence timeout must be positive.")

    materials = load_reading_materials(ROOT / settings["sentence_file"], settings)

    # 사전검사와 사후검사에서 서로 다른 문장 Form 사용
    form = settings["form_by_phase"][logger.phase]
    groups = [(set_id, group.copy()) for set_id, group in materials[form].items()]

    # 동일한 seed에서는 Set 순서가 재현되도록 무작위 배치
    rng = random.Random(f"reading:{seed}:{form}")
    rng.shuffle(groups)
    for _, group in groups:
        rng.shuffle(group)

    screens.wait(kb, draw_screen, screens, "ready")

    try:
        # 하나의 Set에 포함된 문장들을 모두 제시한 뒤 단어 회상 진행
        for set_index, (set_id, group) in enumerate(groups, 1):
            words = []
            progress = f"Set {set_index} / {len(groups)}"

            for item_index, row in enumerate(group, 1):
                trial_info = dict(stage="test", attempt=1, form=form, random_seed=seed,
                                  set_id=set_id, item_id=row["item_id"], sentence=row["sentence"])

                # 문장을 제시하기 전에 해당 문항의 정보를 저장
                logger.write("sentence_start", **trial_info)

                win._resize_draw = lambda: draw_screen(
                    screens, "judgment", f"{progress}   /   Sentence {item_index} / {len(group)}", row["sentence"])
                win._resize_draw()

                # 실제 문장이 화면에 나타나는 시점에 RT 시계 초기화
                win.callOnFlip(kb.clearEvents)
                win.callOnFlip(kb.clock.reset)
                win.flip()

                # 제한 시간 내에 True/False 입력을 받고, 시간이 초과되면 다음 문장으로 진행
                keys = kb.waitKeys(
                    keyList=[settings["true_key"], settings["false_key"], "escape"],
                    waitRelease=False, clear=False, maxWait=timeout,
                )

                key = keys[0] if keys else None

                if key and key.name == "escape":
                    raise KeyboardInterrupt

                # 제한 시간을 초과한 입력은 무응답으로 처리
                if key is not None and key.rt > timeout:
                    key = None

                # 참가자의 판단 결과와 실제 정답을 비교
                correct = key is not None and ((key.name == settings["true_key"]) == row["truth"])

                # 문장 판단의 정답 여부와 관계없이 마지막 단어는 회상 대상에 포함
                words.append(row["recall_word"])

                # 문장별 판단 결과, 반응시간, 시간 초과 여부 기록
                logger.write(
                    "sentence_judgment", **trial_info,
                    expected=row["answer"], recall_word=row["recall_word"],
                    response=key.name if key else None, rt=key.rt if key else None,
                    correct=correct, timed_out=key is None, timeout_s=timeout,
                )

            # Set의 모든 문장이 끝난 뒤 마지막 단어들을 순서대로 입력받음
            recalled, rt = recall_words(win, kb, screens, progress)

            # 실제 마지막 단어들과 참가자의 회상 결과를 비교하여 저장
            logger.write(
                "reading_recall", stage="test", attempt=1, random_seed=seed,
                form=form, set_id=set_id, expected=words, response=recalled, rt=rt,
                **score_recall(words, recalled),
            )
    finally:
        win._resize_draw = None
