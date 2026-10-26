"""PsychoPy와 독립적인 자극 생성: 의도하지 않은 N-back 일치를 방지한다."""

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Trial:
    index: int
    visual: int
    auditory: str
    visual_target: bool
    auditory_target: bool
    warmup: bool


def generate_block(
    n,
    consonants,
    seed=None,
    scored_trials=20,
    visual_targets=6,
    auditory_targets=6,
    simultaneous_targets=2,
):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("N must be an integer of at least 1.")
    if len(consonants) != 8 or len(set(consonants)) != 8:
        raise ValueError("Eight distinct consonants are required.")
    if not (
        0 <= simultaneous_targets <= min(visual_targets, auditory_targets)
        and visual_targets <= scored_trials
        and auditory_targets <= scored_trials
        and visual_targets + auditory_targets - simultaneous_targets <= scored_trials
    ):
        raise ValueError("The target counts are not feasible.")
    rng = random.Random(seed)
    indices = list(range(n, n + scored_trials))
    rng.shuffle(indices)
    both = set(indices[:simultaneous_targets])
    cursor = simultaneous_targets
    visual_only = set(indices[cursor : cursor + visual_targets - simultaneous_targets])
    cursor += visual_targets - simultaneous_targets
    auditory_only = set(
        indices[cursor : cursor + auditory_targets - simultaneous_targets]
    )
    vt, at = both | visual_only, both | auditory_only
    visual, auditory, trials = [], [], []
    for i in range(n + scored_trials):
        # target면 N전 값을 복사, 아니면 N전 값을 후보에서 제외한다.
        v = (
            visual[i - n]
            if i in vt
            else rng.choice([x for x in range(8) if i < n or x != visual[i - n]])
        )
        a = (
            auditory[i - n]
            if i in at
            else rng.choice([x for x in consonants if i < n or x != auditory[i - n]])
        )
        visual.append(v)
        auditory.append(a)
        trials.append(Trial(i, v, a, i in vt, i in at, i < n))
    return trials
