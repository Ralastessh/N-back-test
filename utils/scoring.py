from bisect import bisect_right

# Target 여부와 참가자의 키 입력 여부를 비교하여 네 가지 반응으로 구분
def classify(target, responded):
    if target:
        return "hit" if responded else "miss"
    return "false_alarm" if responded else "correct_rejection"

# 블록별 시각/청각 오류 수에 따라 다음 N-back 난이도를 조절
def adapt_n(n, visual_errors, auditory_errors, *, min_n, decrease_rule, increase_below=3, decrease_above=5):
    if min(n, min_n) < 1 or min(visual_errors, auditory_errors) < 0:
        raise ValueError("Invalid difficulty or error count.")
    if decrease_rule not in ("either", "combined"):
        raise ValueError("decrease_rule must be either or combined.")

    # 두 감각 모두 오류가 3개 미만이면 다음 블록의 n을 1 증가
    if visual_errors < increase_below and auditory_errors < increase_below:
        return n + 1

    # 오류 감소 기준은 감각별 최대 오류 또는 두 감각의 합계 중 선택
    errors = (max(visual_errors, auditory_errors) if decrease_rule == "either" else visual_errors + auditory_errors)

    # 오류가 5개를 초과하면 n을 1 감소시키되 최소 난이도는 유지
    return max(min_n, n - 1) if errors > decrease_above else n

# Digit Span과 Reading Span에서 제시한 순서와 회상한 순서를 비교
def score_recall(expected, recalled):
    # 동일한 위치에서 맞힌 숫자 또는 단어의 개수를 계산
    correct = sum(expected_word == response for expected_word, response in zip(expected, recalled))
    return dict(items_correct=correct, items_total=len(expected), accuracy=correct / len(expected) if expected else 0,
        # 모든 항목의 순서와 개수가 일치해야 완전 정답으로 처리
        exact=list(expected) == list(recalled))

# 한 블록에서 시각과 청각의 정답률을 독립적으로 계산
def nback_summary(errors, total):
    if total < 1 or any(not 0 <= count <= total for count in errors.values()):
        raise ValueError("Invalid scored trial or error count.")
    # 각 감각의 오류 수를 전체 채점 Trial 수에서 빼서 정확도 계산
    return {modality: dict(correct=total - count, incorrect=count, total=total, accuracy=(total - count) / total) for modality, count in errors.items()}

# 키 입력 시각을 기준으로 해당 반응이 어느 Trial에 속하는지 배정
def record_response(records, key, timestamp, key_map, response_window):
    # 실제 자극이 시작된 시각만 모아서 Trial별 기준점으로 사용
    onsets = [r["onset"] for r in records if r["onset"] is not None]

    # 이진 탐색으로 키를 누른 시각보다 이전인 가장 가까운 Trial 시작점 탐색
    index = bisect_right(onsets, timestamp) - 1

    if key not in key_map or index < 0:
        return None

    record = records[index]

    # 현재 Trial의 자극 시작 시점부터 키 입력까지 걸린 시간 계산
    rt = timestamp - record["onset"]

    # 응답 허용 시간을 벗어난 입력은 채점에서 제외
    if not 0 <= rt < response_window:
        return None

    # 같은 감각에 대해 여러 번 입력하더라도 첫 번째 입력인지 구분
    first = not any(r["key"] == key for r in record["responses"])
    record["responses"].append(dict(key=key, rt=rt, first_for_modality=first))


# 각 Trial에서 시각과 청각의 정답 여부를 독립적으로 판정
def trial_outcomes(trial, record, key_map):
    result = {}

    for key, modality in key_map.items():
        # 해당 감각의 첫 번째 키 입력 시간만 가져와 반응 여부 판단
        rt = next((r["rt"] for r in record["responses"] if r["key"] == key), None)

        # N-back Target 여부와 실제 키 입력을 비교하여 Hit/Miss 등을 구분
        outcome = classify(getattr(trial, modality + "_target"), rt is not None)

        result[modality] = dict(
            outcome=outcome,
            rt=rt,
            correct=outcome in ("hit", "correct_rejection"),
        )

    return result

# 실험 중 참가자가 누른 키에 대해서만 정답 피드백 생성
def current_feedback(trial, record, key_map):
    outcomes = trial_outcomes(trial, record, key_map)

    # 아직 입력하지 않은 감각은 피드백을 표시하지 않음
    return {
        modality: "Correct" if result["correct"] else "Incorrect"
        for modality, result in outcomes.items()
        if result["rt"] is not None
    }