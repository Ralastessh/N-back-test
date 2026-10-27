# Jaeggi (2008) PsychoPy 실험 프로젝트

Dual N-back 훈련과 Digit Span·Reading Span 사전/사후검사를 실행합니다. 논문이 명시한 Dual N-back 조건과 수업 프로젝트의 구현 가정을 구분했습니다. Span 과제는 사용자 지정 절차이며 원본 WAIS나 원본 Reading Span 검사의 완전 복제는 아닙니다.

발표 준비는 [PRESENTATION_GUIDE.md](PRESENTATION_GUIDE.md), 변경 내역과 검증 범위는 [VALIDATION.md](VALIDATION.md)를 참고하세요.

## 실행

macOS의 PsychoPy Standalone Coder에서 `main.py`를 열고 Run을 누릅니다. 현재 검증 환경은 PsychoPy 2026.2.4입니다. 별도 Python 환경을 사용한다면 PsychoPy가 지원하는 Python에서 `python -m pip install -r requirements.txt`로 의존성을 설치합니다.

1. 한양대학교 이메일(`student01@hanyang.ac.kr`)과 과제·단계를 선택합니다. 이메일은 형식만 검사하며 실제 계정 소유 인증은 하지 않습니다.
2. Dual N-back은 `training`, Span은 `pretest` 또는 `posttest`를 선택합니다. 잘못 선택하면 경고 후 다시 선택할 수 있습니다.
3. 참가자용 Digit Span은 Forward 고정입니다. 과제 함수의 `mode="backward"` 지원도 유지합니다.
4. 선택한 Span Pretest가 끝나면 Dual N-back Training, Training이 끝나면 같은 Span Posttest를 제안합니다. **SPACE: 계속 / N: 종료**입니다. Training부터 시작하면 같은 이메일의 최근 완료 Pretest를 찾고, 기록이 없으면 D/R 키로 Posttest 검사를 고릅니다.
5. macOS 창의 초록색 전체화면 버튼을 사용할 수 있습니다. 화면 크기는 블록 시작 전에 정하세요. 검사 중 ESC 또는 회상 창 취소는 중단으로 저장됩니다.

각 `tasks/*.py`도 Coder에서 직접 실행할 수 있습니다. PsychoPy가 설치된 터미널 환경에서는 다음과 같이 실행합니다.

```bash
python main.py --task dual_nback --phase training --email student01@hanyang.ac.kr --seed 2008
python tasks/digit_span.py --phase pretest --email student01@hanyang.ac.kr
python tasks/reading_span.py --phase posttest --email student01@hanyang.ac.kr
```

`--fullscreen` / `--windowed`는 CLI에서 사용할 수 있습니다. 화면 크기·음성 장치·타이밍·실험 조건은 `config.py`에서 설정합니다. 실제 실행 전 ABC/English 입력 소스와 헤드폰의 발음·음량을 확인하세요.

## 파일 구조와 읽는 순서

```text
main.py                      참가자 등록, 창 생성, 단계 전환, 저장·종료
config.py                    논문 조건과 구현 가정
 tasks/
   dual_nback.py             프레임 일정 → 키 수집 → 채점 → N 조절
   digit_span.py             숫자열 생성 → 음성 제시 → 순서 회상 → 중단 규칙
   reading_span.py           문항 검증 → 연습 → 문장 판단·단어 회상
 stimuli/
   visual.py                 8개 위치 사각형과 A/L 피드백
   auditory.py               공유 PTB 장치, WAV 사전 로드·예약 재생·소리 확인
   nback_ui.py               기존 안내·카운트다운·10초 휴식·결과 화면
   text.py                   고해상도 글자 렌더링과 사전 캐시
   reading_sentences.csv     영어 연습 P·Pretest A·Posttest B 문항
   reading_review.json       정식 수집 모드의 문항 검토 승인 정보
   audio/                    자음 8개·숫자 9개 WAV와 제작 내역
 utils/
   sequence.py               정확한 target 수를 갖는 N-back 시행 생성
   scoring.py                반응 배정, 감각별·순서별 채점, 난이도 및 집계
   data_logger.py            세션당 반응 CSV 하나, 중단 상태 저장
   span_ui.py                두 Span 과제의 공통 안내·계속/중단
   native_window.py          macOS 기본 전체화면 버튼·Retina 크기 갱신
 tests/                      알고리즘·CSV·모의 실행·타이밍·단계 전환 검증
 tools/generate_audio.py     음성 자극 재제작용 도구
 data/                       실제 반응 CSV (기존 자료 보존)
```

숫자 입력·대기 함수는 `digit_span.py`, 단어 입력·문항 검증·개인별 제한시간 계산은 `reading_span.py`에서 직접 읽을 수 있습니다. 순수 채점과 시퀀스 함수는 PsychoPy 없이 테스트할 수 있습니다.

## 유지한 실험 조건

| 과제 | 조건 |
|---|---|
| Dual N-back | 8개 위치·8개 자음, 동시 제시, 사각형 500ms + ISI 2,500ms, A/L 독립 반응 |
| 시행·target | 블록당 `20 + N` 시행, 세션당 20블록, 감각별 target 6개(동시 target 2개 포함) |
| 반응·채점 | 각 onset 이후 `0 ≤ RT < 3초`, 첫 반응 RT, 반복 키도 보존, hit/miss/false alarm/correct rejection |
| 난이도 | 양쪽 오류가 각각 3 미만이면 N+1, 어느 한쪽 오류가 5 초과면 N−1(최소 1), 나머지는 유지 |
| Digit Span | Forward 3–9 / Backward 2–8, 길이당 2회, 연습 2회, 음성 간격 1초, 같은 길이에서 2회 실패 시 종료 |
| Reading Span | 연습 2문장 × 3세트, 본검사 크기 2·3·4·5 × 각각 3세트, 문장 판단 후 마지막 단어를 순서대로 회상 |

N-back 첫 N개는 warm-up이며 기본적으로 난이도 채점에서 제외합니다. 무반응은 화면에 피드백을 띄우지 않고 시행 종료 후 채점합니다. A/L 반응이 있을 때만 즉시 Correct/Incorrect를 표시합니다. 블록 사이에는 정답·오답·정확도와 다음 N을 보여주고 10초 후 자동 진행합니다.

시행 일정은 키 입력과 무관한 고정 프레임 수로 진행합니다. `win.flip()`의 실제 시각과 키 이벤트 timestamp를 사용하며, PTB에 음성을 미리 예약합니다. 프레임 지연이 생기면 물리적인 제시 시간이 늘어날 수 있으므로 명목 시간과 실제 시간을 구분해야 합니다.

## 데이터와 재현성

과제 실행마다 `data/<task>_YYYY-MM-DD_HH-MM-SS_<임의ID>_responses.csv` 하나를 만듭니다. 시간은 한국 표준시이며 `recorded_kst`는 `YYYY-MM-DD HH:MM:SS`입니다. UTF-8 BOM CSV이므로 Excel에서도 읽을 수 있습니다.

- 공통: `session_id`, `participant`(정규화한 이메일), `task`, `phase`, `stage`, `session_status`, 기록 시각, 이벤트 종류.
- N-back: `block`, `n`, 시행 번호, 자극·target·warm-up·완료/채점 여부, 감각별 최초 RT·정오답·outcome, 전체 유효 키/RT 목록, 블록 오류·정확도와 `next_n`.
- Span: 숫자열 또는 문장·정답·입력·RT, 문장 판단 정오답/시간초과, 회상 위치별 정답 수·정확도·완전 일치. Reading Span에는 `material_status`도 저장합니다.

`session_id`는 **개별 과제 실행** 식별자이며 단계마다 다릅니다. Pre/Training/Post 연결은 같은 `participant`와 `phase`로 합니다. 연구 방문/회차를 묶는 별도 공통 ID는 현재 없습니다.

N-back은 기본적으로 새 seed를 사용하며 `--seed`를 지정하면 시퀀스를 재생성할 수 있습니다. 블록 seed는 기반 seed + 블록 번호입니다. Span은 이메일 SHA-256에서 기반 seed를 구하고 Pre/Post를 구분합니다. **기반 seed 자체는 기존 CSV에 저장하지 않습니다.** 대신 실제 제시된 자극과 target을 저장하여 재채점·시행 분석이 가능합니다.

CSV 생성은 배타 모드이므로 기존 파일을 덮어쓰지 않습니다. 각 행을 쓸 때 flush하고, 정상 종료·ESC·예외 시 세션 상태를 갱신합니다. N-back은 블록의 `finally`에서 시작된 시행을 저장하며 중단된 시행은 미완료로 구분합니다. 강제 프로세스 종료·전원 차단은 이 정리 절차를 보장하지 않습니다. JSONL·시스템 설정·별도 블록/세션 요약 파일은 만들지 않습니다.

## Reading Span 자료 상태

현재 영어 자료는 **미검토 초안**이며 `allow_draft_materials=True`로 개발 실행합니다. 연습 P 6문장, Pretest A와 Posttest B 각각 42문장입니다. 각 A/B의 True 문항 6개에는 사용자 제공 예문을 반영했습니다. 나머지 문장은 기존 초안입니다.

문장 길이·단어 빈도·마지막 단어 난이도 및 A/B의 실제 난이도 동등성은 아직 검토되지 않았습니다. 코드가 검사하는 세트 구성·True/False 균형·대응 ID는 사람의 문항 검토를 대신하지 않습니다. `allow_draft_materials=False`이면 모든 문항의 `reviewed=yes`와 `reading_review.json`의 검토자·난이도 승인·현재 CSV SHA-256을 확인합니다.

## 테스트와 자극 재제작

```bash
python3 -m unittest discover -s tests -v
```

표준 라이브러리만으로 단위·모의 실행 테스트를 수행합니다. 실제 디스플레이·음성·키보드의 정밀 검증과는 구분합니다. 이번 비교 결과와 미검증 항목은 [VALIDATION.md](VALIDATION.md)에 기록했습니다.

자극을 의도적으로 다시 제작해야 할 때만 macOS에서 아래 도구를 실행합니다. 기존 WAV를 교체하므로 현재 자극을 유지하려면 실행하지 않아도 됩니다.

```bash
python3 tools/generate_audio.py
```

제작 조건은 `AUDIO_GENERATION`, 제작 내역은 `stimuli/audio/manifest.json`에 있습니다. 자음은 Capital이라는 안내 없이 알파벳 이름만 발음합니다. 제공된 WAV와 문장 CSV는 이번 리팩토링에서 변경하지 않았습니다.

## 창 크기 변경·전체화면 전환 수정 (2026-10-27)

키 입력을 기다리는 안내 화면에서 크기를 변경하면 화면 내용이 사라지는 현상을 재현해 수정했습니다. `native_window.py`는 새 크기를 보관한 뒤 그리기 context가 준비됐을 때 실제 Retina framebuffer 크기를 반영하며, 전환 중 0 크기는 적용하지 않습니다. N-back 안내·단계 전환·Span 화면에는 재그리기 함수를 등록해 대기 중에도 표시를 복원합니다. 재그리기에서는 RT 시계와 예약된 `win.flip()` 콜백을 다시 실행하지 않습니다.

실제 PsychoPy 2026.2.4에서 안내·단계 전환·Span 화면의 자동 크기 변경과 macOS 전체화면 왕복 후 표시를 확인했습니다. 0 크기·지연 갱신·대기 화면 정리 등 임시 회귀 검사 4개도 통과했습니다. 창 크기 변경 후 실제 N-back 4시행에서도 사각형 약 500ms·시행 간격 약 3초와 늦은 반응 RT 기록이 유지됐습니다. 실제 마우스 드래그로 보고된 크래시 자체는 재현하지 못했으며, 마우스 자동 조작 검사는 실험 창의 접근성 응답 문제로 완료하지 못했습니다. 검사는 임시 스크립트로 수행했고 연구 데이터 파일은 생성하지 않았습니다.

수정 코드를 적용하려면 기존 실험 프로세스를 종료하고 `main.py`를 새로 실행하세요. 실험 타이밍을 유지하려면 화면 크기는 블록 시작 전에 정합니다.

전체화면 전환 시 A/L 박스만 위로 이동하던 문제도 수정했습니다. 고정 사각형이 생성 시점의 픽셀 좌표·크기를 보관하므로, 화면 크기가 바뀌면 원래 height 단위 좌표·크기를 다시 적용합니다. 시각 자극 사각형의 크기도 같은 방식으로 갱신합니다. 실제 창 모드(2000×1600 framebuffer) → 전체화면(4480×2520) → 창 모드 복귀에서 박스 중심·크기가 같고, 글자가 박스 안에 있으며 하단 자극과 0.055 height 간격을 유지하는 것을 확인했습니다. 창 연결은 별도의 AppKit 객체로 다시 감싸지 않고 pyglet가 소유한 창을 직접 사용하도록 정리했으며, 최종 왕복 검사에서는 앞서 관찰된 창 이벤트 오류가 나타나지 않았습니다.
