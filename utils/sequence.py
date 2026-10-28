from dataclasses import dataclass
import random

# 각 Trial에서 제시할 시각/청각 자극과 Target 여부를 하나의 데이터로 관리
@dataclass(frozen=True)
class Trial:
    index: int
    visual: int
    auditory: str
    visual_target: bool
    auditory_target: bool
    warmup: bool

# N-back 수준에 따라 시각과 청각 자극의 순서를 생성
def generate_block(n, consonants, seed=None, scored_trials=20, visual_targets=6, auditory_targets=6, simultaneous_targets=2):
    # N-back 비교가 가능하도록 n은 1 이상의 정수로 제한
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("N must be an integer of at least 1.")

    # 원본 논문의 실험 조건에 맞춰 서로 다른 8개의 자음 사용
    if len(consonants) != 8 or len(set(consonants)) != 8:
        raise ValueError("Eight distinct consonants are required.")

    # Target 개수가 전체 Trial 수를 초과하거나 서로 모순되지 않도록 검사
    if not (
        0 <= simultaneous_targets <= min(visual_targets, auditory_targets)
        and visual_targets <= scored_trials
        and auditory_targets <= scored_trials
        and visual_targets + auditory_targets - simultaneous_targets <= scored_trials
    ):
        raise ValueError("The target counts are not feasible.")

    # 동일한 seed를 사용하면 같은 자극 순서를 재현할 수 있도록 설정
    rng = random.Random(seed)

    # 처음 n개의 Warm-up을 제외한 20개 Trial에서 Target 위치를 결정
    indices = list(range(n, n + scored_trials))
    rng.shuffle(indices)

    # 시각과 청각이 동시에 일치하는 Target 2개를 먼저 배정
    both = set(indices[:simultaneous_targets])
    cursor = simultaneous_targets

    # 시각 자극만 일치하는 Target 4개 배정
    visual_only = set(indices[cursor : cursor + visual_targets - simultaneous_targets])
    cursor += visual_targets - simultaneous_targets

    # 청각 자극만 일치하는 Target 4개 배정
    auditory_only = set(indices[cursor : cursor + auditory_targets - simultaneous_targets])

    # 각 감각의 Target에는 단독 Target과 동시 Target을 모두 포함
    vt, at = both | visual_only, both | auditory_only
    visual, auditory, trials = [], [], []

    # 초기 n개의 자극과 실제 평가할 20개 자극을 합쳐 총 20+n Trial 생성
    for i in range(n + scored_trials):
        # 시각 Target이면 n번 전 위치를 그대로 사용
        # Non-target이면 n번 전 위치를 제외한 나머지 7개 위치 중 무작위 선택
        v = (visual[i - n] if i in vt else rng.choice([x for x in range(8) if i < n or x != visual[i - n]]))

        # 청각 Target이면 n번 전 자음을 그대로 사용
        # Non-target이면 n번 전 자음을 제외하여 의도하지 않은 일치 방지
        a = (auditory[i - n] if i in at else rng.choice([x for x in consonants if i < n or x != auditory[i - n]]))

        visual.append(v)
        auditory.append(a)

        # 현재 Trial의 자극, Target 여부, Warm-up 여부를 함께 저장
        trials.append(Trial(i, v, a, i in vt, i in at, i < n))

    return trials
