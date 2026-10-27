"""문장 의미 판단 + 마지막 단어 순서 회상. 초안/승인 상태를 CSV에 구분한다."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import csv
import hashlib
import json
import random
from statistics import mean, stdev
from config import ROOT, READING_SPAN
from utils.scoring import reading_summary
from utils.scoring import score_recall
from utils.span_ui import show, pause



def load_reading_materials(path, settings, review_path, require_review=True):
    """세트 구성·정답 균형·A/B 대응을 검사한다. 정식 모드는 문항 승인도 확인한다."""
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    groups = {form: {} for form in ("A", "B", "P")}
    ids = set()
    for row in rows:
        form = row["form"]
        if form not in groups:
            raise ValueError("Form must be A, B, or P.")
        if not row["item_id"] or row["item_id"] in ids:
            raise ValueError("Duplicate or missing item_id.")
        ids.add(row["item_id"])
        if row["answer"] not in ("True", "False"):
            raise ValueError("Answer must be True or False.")
        row["truth"] = row["answer"] == "True"
        if not row["sentence"].strip() or not row["recall_word"].strip():
            raise ValueError("Empty sentence or recall word.")
        if int(row["word_count"]) != len(row["sentence"].split()):
            raise ValueError(f'{row["item_id"]}: update word_count.')
        final = row["sentence"].strip().split()[-1].rstrip(".!?。")
        if final != row["recall_word"]:
            raise ValueError(
                f'{row["item_id"]}: recall_word does not match the final word.'
            )
        if require_review and row["reviewed"] != "yes":
            raise ValueError("Unreviewed item: " + row["item_id"])
        groups[form].setdefault(row["set_id"], []).append(row)
    for form, sets in groups.items():
        expected = (
            [settings["practice_set_size"]] * settings["practice_sets"]
            if form == "P"
            else [
                n for n in settings["lengths"] for _ in range(settings["sets_per_size"])
            ]
        )
        if sorted(map(len, sets.values())) != sorted(expected):
            raise ValueError(f"{form}: invalid set composition.")
        truths = []
        for group in sets.values():
            group.sort(key=lambda r: int(r["item_order"]))
            if [int(r["item_order"]) for r in group] != list(range(1, len(group) + 1)):
                raise ValueError("Invalid item_order.")
            if any(int(r["set_size"]) != len(group) for r in group):
                raise ValueError("Invalid set_size.")
            truths.extend(r["truth"] for r in group)
        if sum(truths) * 2 != len(truths):
            raise ValueError(f"{form}: True/False counts are not balanced.")
    # A/B는 pair_id별 길이·순서·정답을 대응시킨다. 난이도 동등성은 별도 인간 검토.
    a = {r["pair_id"]: r for r in rows if r["form"] == "A"}
    b = {r["pair_id"]: r for r in rows if r["form"] == "B"}
    if (
        len(a) != sum(map(len, groups["A"].values()))
        or len(b) != sum(map(len, groups["B"].values()))
        or set(a) != set(b)
    ):
        raise ValueError("A/B pair_id mismatch or duplicate.")
    for key in a:
        if any(a[key][k] != b[key][k] for k in ("set_size", "item_order", "answer")):
            raise ValueError("A/B paired item structure does not match.")
    if require_review:
        review = json.loads(Path(review_path).read_text(encoding="utf-8"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if (
            not review.get("forms_difficulty_reviewed")
            or review.get("approved_csv_sha256") != digest
            or not review.get("reviewer")
        ):
            raise ValueError(
                "Review A/B difficulty matching and approve the current CSV hash before running."
            )
    return groups

def practice_timeout(rts, multiplier=2.5, minimum=2):
    """개인별 읽기 속도에 맞춰 정답 연습 RT의 평균 + 배수 × 표본 SD를 사용한다."""
    if len(rts) < minimum:
        raise ValueError("Too few correct practice RTs: repeat practice.")
    if any(rt <= 0 for rt in rts):
        raise ValueError("RT must be positive.")
    return mean(rts) + multiplier * stdev(rts)


def recall_words(win):
    from psychopy import gui, core

    clock = core.Clock()
    win.callOnFlip(clock.reset)
    show(
        win,
        "Recall the final words in order.\nSeparate words with spaces. Enter _ for each missing position.",
    )
    dialog = gui.Dlg(title="Serial word recall")
    dialog.addField("Words (spaces between words; _ for a missing word):", "")
    values = dialog.show()
    if not dialog.OK:
        raise KeyboardInterrupt
    response = values[0].strip().split()
    return response, clock.getTime()


def run(win, logger, seed):
    from psychopy.hardware import keyboard

    kb = keyboard.Keyboard()
    settings = READING_SPAN
    if settings["early_stopping"]:
        raise ValueError("Reading Span uses all sets; early stopping is not supported.")
    if settings["min_correct_practice_rts"] < 2:
        raise ValueError(
            "At least two correct practice RTs are required for a sample SD."
        )
    draft = settings["allow_draft_materials"]
    materials = load_reading_materials(
        ROOT / settings["sentence_file"], settings, ROOT / settings["review_file"],
        require_review=not draft,
    )
    material_status = "draft" if draft else "approved"

    def write(kind, **fields):
        logger.write(kind, material_status=material_status, **fields)

    form = settings["form_by_phase"][logger.phase]

    def run_sets(groups, stage, timeout, attempt=1):
        recalls = []
        judgments = []
        correct_rts = []
        for set_id, group in groups:
            words = []
            for row in group:
                write(
                    "sentence_start",
                    stage=stage,
                    attempt=attempt,
                    form=row["form"],
                    set_id=set_id,
                    item_id=row["item_id"],
                    sentence=row["sentence"],
                )
                win.callOnFlip(kb.clearEvents)
                win.callOnFlip(kb.clock.reset)
                show(
                    win,
                    row["sentence"]
                    + "\n\nTrue: "
                    + settings["true_key"].upper()
                    + " / False: "
                    + settings["false_key"].upper(),
                )
                keys = kb.waitKeys(
                    keyList=[settings["true_key"], settings["false_key"], "escape"],
                    waitRelease=False,
                    clear=False,
                    maxWait=timeout,
                )
                key = keys[0] if keys else None
                if key is not None and key.name != "escape" and key.rt > timeout:
                    key = None
                if key and key.name == "escape":
                    raise KeyboardInterrupt
                correct = key is not None and (
                    (key.name == settings["true_key"]) == row["truth"]
                )
                judgments.append(correct)
                if correct:
                    correct_rts.append(key.rt)
                words.append(row["recall_word"])
                write(
                    "sentence_judgment",
                    stage=stage,
                    attempt=attempt,
                    form=row["form"],
                    set_id=set_id,
                    item_id=row["item_id"],
                    sentence=row["sentence"],
                    expected=row["answer"],
                    recall_word=row["recall_word"],
                    response=key.name if key else None,
                    rt=key.rt if key else None,
                    correct=correct,
                    timed_out=key is None,
                    timeout_s=None if timeout == float("inf") else timeout,
                )
            recalled, rt = recall_words(win)
            score = score_recall(words, recalled)
            recalls.append(score)
            write(
                "reading_recall",
                stage=stage,
                attempt=attempt,
                form=group[0]["form"],
                set_id=set_id,
                expected=words,
                response=recalled,
                rt=rt,
                **score,
            )
            if stage == "practice":
                pause(win, "Correct recall: " + " / ".join(words), kb)
        write(
            "reading_summary",
            stage=stage,
            attempt=attempt,
            form=form if stage == "test" else "P",
            **reading_summary(recalls, judgments, settings["processing_flag_below"]),
        )
        return correct_rts

    pause(
        win,
        ("Reading Span practice [DRAFT MATERIALS]" if draft else "Reading Span practice")
        + "\nJudge whether each sentence is plausible. Remember its final word.\nRecall the final words in order. Use _ for a missing word.",
        kb,
    )
    attempt = 1
    while True:
        rts = run_sets(list(materials["P"].items()), "practice", float("inf"), attempt)
        if len(rts) >= settings["min_correct_practice_rts"]:
            break
        pause(
            win,
            "Not enough correct practice responses. Please repeat the practice.",
            kb,
        )
        attempt += 1
    timeout = practice_timeout(
        rts, settings["timeout_sd_multiplier"], settings["min_correct_practice_rts"]
    )
    groups = list(materials[form].items())
    if settings["randomized_set_order"]:
        random.Random(f"{seed}:{form}").shuffle(groups)
    pause(win, ("Draft test" if draft else "The test")
          + " will now begin. Each sentence has a time limit.", kb)
    run_sets(groups, "test", timeout)


if __name__ == "__main__":
    from main import main

    main(default_task="reading_span")
