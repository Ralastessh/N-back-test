"""오류는 modality별 miss + false_alarm. 반복 키는 원자료에 남기고 1회로 채점."""


def classify(target, responded):
    return (
        ("hit" if responded else "miss")
        if target
        else ("false_alarm" if responded else "correct_rejection")
    )


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
    correct = sum(
        i < len(recalled) and word == recalled[i] for i, word in enumerate(expected)
    )
    return dict(
        items_correct=correct,
        items_total=len(expected),
        accuracy=correct / len(expected) if expected else 0,
        exact=list(expected) == list(recalled),
    )
