"""문장 의미 판단 + 마지막 어절 순서 회상. 검토 승인된 CSV만 본검사에 사용."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import random
from config import ROOT, READING_SPAN
from utils.span_protocol import (
    load_reading_materials,
    practice_timeout,
    reading_summary,
)
from utils.scoring import score_recall
from utils.span_ui import show, pause, recall_words


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
    write(
        "reading_timeout", correct_practice_rts=rts, timeout_s=timeout, attempt=attempt
    )
    groups = list(materials[form].items())
    if settings["randomized_set_order"]:
        random.Random(f"{seed}:{form}").shuffle(groups)
    write("reading_order", form=form, set_order=[key for key, _ in groups])
    pause(win, ("Draft test" if draft else "The test")
          + " will now begin. Each sentence has a time limit.", kb)
    run_sets(groups, "test", timeout)


if __name__ == "__main__":
    from main import main

    main(default_task="reading_span")
