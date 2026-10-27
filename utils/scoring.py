"""화면과 독립적인 반응 배정·채점. 감각별 오류는 miss + false alarm."""

from bisect import bisect_right


def classify(target, responded):
    if target:
        return "hit" if responded else "miss"
    return "false_alarm" if responded else "correct_rejection"


def adapt_n(
    n,
    visual_errors,
    auditory_errors,
    *,
    min_n,
    decrease_rule,
    increase_below=3,
    decrease_above=5
):
    if min(n, min_n) < 1 or min(visual_errors, auditory_errors) < 0:
        raise ValueError("Invalid difficulty or error count.")
    if decrease_rule not in ("either", "combined"):
        raise ValueError("decrease_rule must be either or combined.")
    if visual_errors < increase_below and auditory_errors < increase_below:
        return n + 1
    errors = (
        max(visual_errors, auditory_errors)
        if decrease_rule == "either"
        else visual_errors + auditory_errors
    )
    return max(min_n, n - 1) if errors > decrease_above else n


def score_recall(expected, recalled):
    """단어·숫자는 같은 순서 위치끼리 비교한다. 추가 응답도 완전 정답에서 제외한다."""
    correct = sum(
        i < len(recalled) and word == recalled[i] for i, word in enumerate(expected)
    )
    return dict(
        items_correct=correct,
        items_total=len(expected),
        accuracy=correct / len(expected) if expected else 0,
        exact=list(expected) == list(recalled),
    )


def nback_summary(errors, total):
    """감각별 전체 정확도: hit+correct rejection / 채점 완료 시행 수."""
    if total < 1 or any(not 0 <= count <= total for count in errors.values()):
        raise ValueError("Invalid scored trial or error count.")
    return {modality: dict(correct=total - count, incorrect=count, total=total,
                           accuracy=(total - count) / total)
            for modality, count in errors.items()}


def record_response(records, key, timestamp, key_map, response_window):
    """이벤트 발생 시각으로 배정한다. 다음 프레임에 수집된 이전 시행 키도 보존한다."""
    onsets = [r["onset"] for r in records if r["onset"] is not None]
    index = bisect_right(onsets, timestamp) - 1
    if key not in key_map or index < 0:
        return None
    record = records[index]
    rt = timestamp - record["onset"]
    if not 0 <= rt < response_window:
        return None
    modality = key_map[key]
    first = not any(r["key"] == key for r in record["responses"])
    record["responses"].append(dict(key=key, rt=rt, first_for_modality=first))
    return index, modality, first


def trial_outcomes(trial, record, key_map):
    result = {}
    for key, modality in key_map.items():
        rts = [r["rt"] for r in record["responses"] if r["key"] == key]
        outcome = classify(getattr(trial, modality + "_target"), bool(rts))
        result[modality] = dict(
            outcome=outcome,
            rt=rts[0] if rts else None,
            correct=outcome in ("hit", "correct_rejection"),
        )
    return result


def current_feedback(trial, record, key_map):
    """실제로 누른 감각만 화면에 표시한다. 무응답은 채점에만 사용한다."""
    outcomes = trial_outcomes(trial, record, key_map)
    return {
        modality: "Correct" if result["correct"] else "Incorrect"
        for modality, result in outcomes.items()
        if result["rt"] is not None
    }


def span_summary(rows):
    """숫자열 전체가 일치한 시행 수와 정답을 얻은 최대 길이."""
    exact = sum(r["exact"] for r in rows)
    return dict(
        trials=len(rows),
        exact_serial_accuracy=exact / len(rows) if rows else 0,
        maximum_span=max((r["length"] for r in rows if r["exact"]), default=0),
        total_correct=exact,
    )


def reading_summary(rows, judgments, threshold):
    """문장 판단과 회상을 분리한다. 세트 평균과 전체 단어 비율도 구분한다."""
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
