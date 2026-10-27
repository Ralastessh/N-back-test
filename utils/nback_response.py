"""프레임 갱신과 독립적인 키 이벤트 배정·채점. RT의 단위는 초."""

from bisect import bisect_right
from utils.scoring import classify

OUTCOME_LABELS = {
    "hit": "Correct",
    "miss": "Incorrect",
    "correct_rejection": "Correct",
    "false_alarm": "Incorrect",
}


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
        modality: OUTCOME_LABELS[result["outcome"]]
        for modality, result in outcomes.items()
        if result["rt"] is not None
    }
