# 작업기억 실험 프로젝트

Jaeggi et al. (2008)을 바탕으로 Dual N-back 훈련과 작업기억 사전·사후검사를 실행하는 PsychoPy 프로그램입니다.

- **Dual N-back:** 시각 위치와 청각 알파벳을 N개 전 자극과 비교합니다. A는 시각, L은 청각 반응이며 수행 결과에 따라 N이 조절됩니다.
- **Digit Span:** 들려준 숫자를 순서대로 입력하는 검사입니다. 연습 없이 본검사만 진행합니다.
- **Reading Span:** 문장의 타당성을 Y/N으로 판단하고, 각 문장의 마지막 단어를 순서대로 회상합니다. 연습 없이 본검사만 진행하며 문장 판단 제한시간은 5초입니다. 현재 문항은 개발용 초안입니다.

## 퀵스타트

실행 환경은 **macOS · PsychoPy Standalone 2026.2.4**입니다.

1. 헤드폰을 연결하고 키보드 입력 소스를 **ABC/English**로 설정합니다.
2. PsychoPy의 **Coder**에서 이 폴더의 [main.py](main.py)를 열고 **Run**을 누릅니다.
3. 한양대학교 이메일(`이름@hanyang.ac.kr`)을 입력합니다. 이메일은 참가자 구분에 사용하며 형식만 확인합니다.
4. `task`와 `phase`를 아래처럼 선택합니다.

   | 실행할 검사 | task | phase |
   |---|---|---|
   | Dual N-back 훈련 | `dual_nback` | `training` |
   | Digit Span 사전·사후검사 | `digit_span` | `pretest` 또는 `posttest` |
   | Reading Span 사전·사후검사 | `reading_span` | `pretest` 또는 `posttest` |

5. 화면 안내에 따라 진행합니다. 전체화면은 macOS 창의 초록색 버튼을 사용하고, 화면 크기는 블록 시작 전에 정합니다. **ESC**로 중단할 수 있습니다.

선택한 Span의 Pretest가 끝나면 Dual N-back Training, Training이 끝나면 같은 Span의 Posttest 진행을 제안합니다. **SPACE는 계속, N은 종료**입니다. 각 검사를 따로 실행할 수도 있습니다.

PsychoPy가 설치된 터미널 환경에서도 실행하면 동일한 시작 선택창이 열립니다.

```bash
python main.py
```

실험 설정은 [config.py](config.py)에서 변경합니다.

## 결과 확인

결과는 프로젝트의 **[data/](data/)** 폴더에 자동 저장됩니다. 각 과제 실행마다 반응 CSV 하나를 생성하며, Excel에서 열어 확인할 수 있습니다.

```text
data/dual_nback_2026-10-27_22-15-00_ab12cd34_responses.csv
```

파일명의 날짜·시각과 `recorded_kst`는 **한국시간, 24시간제**입니다. 실행이 끝나면 Coder 출력창에도 저장 경로가 표시됩니다.

주요 확인 항목은 다음과 같습니다.

| 항목 | CSV에서 확인할 내용 |
|---|---|
| 참가자·검사 단계 | `participant`, `task`, `phase`, `stage`(본검사) |
| N-back 블록·난이도 | `block`, `n`, `next_n` |
| 자극·실제 반응·RT | 시각 위치·청각 알파벳, 숫자열·문장, 입력한 키·응답, 반응시간(초) |
| 정오답·정확도 | 감각별 정오답·블록 정확도, 문장 판단 결과·회상 정답 수 |
| 종료 상태 | `session_status`: `completed`(완료), `aborted`(중단), `error`(오류) |

같은 사람의 사전검사·훈련·사후검사는 **동일한 이메일의 `participant` 값**으로 연결합니다. `session_id`는 과제를 실행할 때마다 달라집니다. N-back 결과는 `block` 열로 필터링하여 블록별로 확인할 수 있습니다.
