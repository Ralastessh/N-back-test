"""화면 없는 검사 설계·채점. 실험 실행과 분리해 단위 테스트 가능."""

import csv
import hashlib
import json
import random
from statistics import mean, stdev
from pathlib import Path


def digit_plans(seed, settings):
    rng = random.Random(f"digit:{seed}")
    used, plans = set(), {}
    for phase in ("pretest", "posttest"):
        for mode in ("forward", "backward"):
            for stage in ("practice", "test"):
                lengths = (
                    settings[mode + "_lengths"][:1] * settings["practice_trials"]
                    if stage == "practice"
                    else [
                        n
                        for n in settings[mode + "_lengths"]
                        for _ in range(settings["trials_per_length"])
                    ]
                )
                sequences = []
                for length in lengths:
                    for attempt in range(10000):
                        digits = []
                        for _ in range(length):
                            candidates = [
                                str(d)
                                for d in settings["digit_pool"]
                                if settings["adjacent_repetitions"]
                                or not digits
                                or str(d) != digits[-1]
                            ]
                            if not candidates:
                                raise ValueError("No eligible digit candidates.")
                            digits.append(rng.choice(candidates))
                        key = tuple(digits)
                        if key not in used:
                            break
                    else:
                        raise ValueError(
                            "Cannot generate unique sequences with these settings."
                        )
                    used.add(key)
                    sequences.append(digits)
                plans[(phase, mode, stage)] = sequences
    return plans


def expected_recall(digits, mode):
    if mode not in ("forward", "backward"):
        raise ValueError("Choose forward or backward.")
    return list(digits) if mode == "forward" else list(reversed(digits))


def span_summary(rows):
    exact = sum(r["exact"] for r in rows)
    return dict(
        trials=len(rows),
        exact_serial_accuracy=exact / len(rows) if rows else 0,
        maximum_span=max((r["length"] for r in rows if r["exact"]), default=0),
        total_correct=exact,
    )


def practice_timeout(rts, multiplier=2.5, minimum=2):
    if len(rts) < minimum:
        raise ValueError("Too few correct practice RTs: repeat practice.")
    if any(rt <= 0 for rt in rts):
        raise ValueError("RT must be positive.")
    return mean(rts) + multiplier * stdev(rts)


def reading_summary(rows, judgments, threshold):
    processing = sum(judgments) / len(judgments) if judgments else 0
    return dict(
        processing_accuracy=processing,
        processing_trials=len(judgments),
        processing_correct=sum(judgments),
        processing_below_threshold=processing < threshold,
        position_correct_partial_credit=(
            sum(r["accuracy"] for r in rows) / len(rows) if rows else 0
        ),
        complete_set_accuracy=sum(r["exact"] for r in rows) / len(rows) if rows else 0,
        item_accuracy=(
            sum(r["items_correct"] for r in rows) / sum(r["items_total"] for r in rows)
            if rows
            else 0
        ),
        sets=len(rows),
    )


def load_reading_materials(path, settings, review_path, require_review=True):
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
