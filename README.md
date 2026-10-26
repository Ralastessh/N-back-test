# Jaeggi (2008) PsychoPy 과제 재현 프로젝트

학부 수준에서 코드를 설명하고 수정할 수 있도록 자극 생성, 제시, 채점, 저장을 나눈 프로젝트입니다. Dual N-back의 명시된 조건은 원문을 따르며, Span 검사는 사용자가 지정한 절차로 구현했습니다. **원본 WAIS 또는 원본 Reading Span 검사를 완전히 복제한 검사가 아닙니다.**

Reading Span의 영어 문장은 **미검토 초안**입니다. A/B 각 42문장과 연습용 6문장이 있으나, 문항 검토 및 A/B 난이도 대응 검토 전에는 실행되지 않습니다. 구조를 맞춘 것이 경험적 난이도 동등성을 입증하지는 않습니다.


## 수정 사항: 영어 화면·시행 중 피드백·청각 출력 확인

현재 실행 코드는 프로젝트 최상위 `main.py`, `tasks/`에 있습니다. `PROTOCOL_VERSION`은 `2026-10-26-english-feedback-v2`이며 세션 설정에 기록됩니다.

- 화면 안내, 입력창, 반응 피드백, 실행 오류 메시지는 영어입니다. Reading Span 활성 CSV도 영어 초안으로 바꿨으며 `reviewed=no`를 유지합니다. 이전 한국어 초안은 `stimuli/archive/`에 보존했으며 프로그램은 읽지 않습니다. 한국어 코드 주석과 이 설명서는 코드 학습을 위해 유지했습니다.
- **A는 시각 위치가 N개 전과 일치할 때, L은 청각 자음이 N개 전과 일치할 때** 누릅니다. 둘 다 일치하면 두 키, 둘 다 불일치하면 무반응입니다.
- 응답 가능한 구간은 각 시행의 **0 ≤ RT < 3초**입니다. 500ms 후 사각형이 사라져도 계속 응답할 수 있습니다. 예를 들어 2.7초의 A 반응은 그 시행에 속하며 다음 시행은 원래 일정대로 진행됩니다.
- 첫 유효 A/L 키 반응 뒤 다음 화면 갱신에서 해당 감각의 `Correct (Hit)` 또는 `Incorrect (False Alarm)`을 표시합니다. 양쪽 감각은 별도로 표시됩니다. 반복 입력은 원자료에 남기되 점수와 최초 RT를 바꾸지 않습니다.
- 무응답의 정오는 3초가 끝난 뒤에만 확정합니다. Target 무응답은 `Incorrect (Miss)`, Non-target 무응답은 `Correct (Correct Rejection)`입니다. 다음 시행 하단에 `Previous trial` 결과를 0.75초 동안 표시합니다. 이 표시를 위해 다음 자극을 지연시키지 않습니다. 마지막 시행 결과는 블록 요약에 표시됩니다.
- `NBACK_FEEDBACK`에서 피드백 사용 여부와 이전 결과 표시 시간을 바꿀 수 있습니다. **시행 중 즉시 피드백은 사용자가 추가한 조건이며, 원논문 본문에 명시된 조건이라고 주장하지 않습니다.**
- 첫 N개는 기억을 채우는 준비 시행이며, 그 뒤 **채점 시행 20개**가 진행됩니다. 화면에 `Warm-up` / `Trial 1/20` 등을 구분합니다. 준비 시행의 반응 피드백은 표시하되 적응 난이도 채점에서는 제외합니다.
- 자음은 공유 PTB 출력 장치에서 미리 로드하고 사각형과 같은 onset에 예약합니다. `audio_scheduled_ptb`와 `audio_backend`의 시작 시각을 함께 저장합니다. 백엔드 기록이 실제 귀에 들린 시각을 보증하지는 않습니다.
- 시작 전 **Audio check**에서 자음 8개를 듣습니다. 모두 들렸으면 SPACE, 다시 들으려면 R, 출력 장치를 바꾸려면 D를 누릅니다. 들리지 않으면 D로 헤드폰/스피커를 선택하고 시스템 음량·음소거를 확인하세요. 선택한 장치와 청취 확인 여부는 `*_audio_check.csv`에 기록됩니다.
- `AUDIO_PLAYBACK`의 `device_name`, `volume`, `schedule_lead_s`를 설정할 수 있습니다. `check_before_session=False`는 자동 기술 검사에만 사용하고, 실제 수집에서는 청취 확인을 유지하세요.
- 피드백은 `*_trial.csv`의 `feedback_events`, 이전 시행 결과 표시 시각은 `result_display_onset`에 기록됩니다. 표시 시각은 블록 시작 기준 초입니다. 마지막 시행의 블록 요약 표시는 별도 RT 측정 대상이 아닙니다.

| 실제 상태 | A 또는 L의 해당 감각 반응 | 결과 |
|---|---|---|
| Target (일치) | 3초 내 해당 키 | Hit — Correct |
| Target (일치) | 무응답 | Miss — Incorrect |
| Non-target (불일치) | 무응답 | Correct Rejection — Correct |
| Non-target (불일치) | 해당 키 | False Alarm — Incorrect |

실제 화면은 디스플레이 프레임에 맞춰 갱신되므로 3초는 명목 일정입니다. 키 입력·피드백 때문에 멈추거나 조기 종료하지 않지만, 운영체제/디스플레이 지연은 실제 flip 기록에서 확인해야 합니다.

## 빠른 실행: macOS PsychoPy Coder

1. [공식 설치 페이지](https://psychopy.org/download.html)에서 macOS용 **PsychoPy Standalone**을 설치합니다. 이 컴퓨터의 Standalone **2026.2.4**로 실제 실행을 검사했습니다. 시스템 Python과 Standalone에 내장된 Python은 서로 다를 수 있습니다.
2. PsychoPy를 열고 Coder에서 이 폴더의 `main.py`를 엽니다. Run을 누릅니다.
3. `participant`에는 익명 ID(예: `P001`), `task`에는 과제를 선택합니다. Dual N-back은 `phase=training`, Span은 `pretest` 또는 `posttest`를 선택합니다.
4. Digit Span은 `mode=forward` 또는 `backward`를 골라 **각각 별도로 실행**합니다. 두 방향의 중단 규칙과 점수는 독립적입니다.
5. 실제 실험은 헤드폰을 연결하여 17개 음성의 발음·음량을 확인한 뒤 시작합니다. 작업용 창 모드가 기본이며 크기와 전체 화면은 `config.py`의 `DISPLAY`에서 변경합니다.
6. 데이터는 실행 위치와 관계없이 이 프로젝트의 `data/`에 저장됩니다. ESC 또는 회상 입력창의 취소는 중단으로 기록됩니다.

PsychoPy가 설치된 Python 환경에서는 다음 명령도 가능합니다.

```bash
python main.py --task dual_nback --participant P001 --phase training
python tasks/digit_span.py --participant P001 --phase pretest --mode forward
python tasks/digit_span.py --participant P001 --phase posttest --mode backward
python tasks/reading_span.py --participant P001 --phase pretest
```

각 `tasks/*.py`를 Coder에서 직접 실행할 수도 있습니다. 선택창이 열리면 Span의 phase를 pretest/posttest로 지정하세요. 터미널의 `python`에 PsychoPy가 없다면 Coder를 사용하세요. 별도 환경을 만들 때는 설치하려는 PsychoPy 버전의 지원 Python을 공식 설치 페이지에서 확인하고 `python -m pip install -r requirements.txt`로 설치합니다. Standalone에서는 추가 pip 설치가 필요하지 않습니다.

실행 전 macOS 입력 소스를 ABC/English로 선택하세요. 검사 중 입력기 콜백 경고가 관찰되어 실제 A/L 키 입력을 사전 점검해야 합니다. macOS가 입력 모니터링 권한을 요청하면 실험에 사용하는 PsychoPy 앱에 권한을 부여하고 앱을 다시 시작합니다. 소리 장치는 PsychoPy Preferences의 Hardware에서 확인하세요. 본 구현은 PTB 예약 재생을 사용하며, 실패할 때 다른 오디오 엔진으로 자동 전환하지 않습니다.

## 파일을 읽는 순서

| 파일 | 설명할 때의 핵심 질문 |
|---|---|
| `config.py` | 논문 조건과 사용자 지정 조건은 무엇인가? |
| `utils/sequence.py` | 정확히 6/6/2 target을 어떻게 만들고 우연한 target을 막는가? |
| `utils/scoring.py` | hit, miss, false alarm, correct rejection을 어떻게 구분하는가? |
| `tasks/dual_nback.py` | 하나의 프레임 루프에서 두 자극과 반응 시간을 어떻게 관리하는가? |
| `stimuli/visual.py`, `stimuli/auditory.py` | 사각형 그리기와 WAV 준비·재생은 어떻게 분리되는가? |
| `utils/span_protocol.py` | 숫자 시퀀스, 연습 RT 제한시간, 문항 검토, 점수는 어떻게 계산하는가? |
| `tasks/digit_span.py`, `tasks/reading_span.py` | 각 검사에서 어떤 순서로 제시·입력·채점하는가? |
| `utils/span_ui.py` | 숫자 키 입력과 영어 단어 회상 입력창은 어떻게 작동하는가? |
| `utils/data_logger.py` | 원자료를 CSV와 JSONL에 어떻게 보존하는가? |
| `tests/` | 과제 논리가 요구 조건을 충족하는지 어떻게 확인하는가? |

### Dual N-back의 핵심 흐름

1. 20개 채점 가능 위치를 섞고, 동시 target 2개·시각만 4개·청각만 4개를 배정합니다. 첫 N개는 비교할 과거 자극이 없는 준비 시행입니다.
2. target 위치에서는 해당 감각의 N개 전 값을 복사합니다. non-target 위치에서는 N개 전 값을 후보에서 **제외**하고 선택합니다. 따라서 우연한 추가 target이 생기지 않습니다.
3. 실제 화면 flip 간격의 중앙값을 측정해 500ms 제시와 2,500ms ISI를 각각 프레임 수로 환산합니다. 화면은 프레임 단위이므로 임의 시간값은 가까운 프레임으로 양자화됩니다.
4. `dual_nback.py`가 약 100ms 앞서 PTB 시각으로 오디오를 예약하고, 같은 프레임 일정에 사각형을 그립니다. 음성 파일은 블록 전에 로드합니다.
5. 각 감각에서 첫 유효 키 반응으로 반응 유무와 RT를 정하고, 반복 키도 원자료에 남깁니다. RT는 해당 시각 자극 시작 기준 초입니다. 각 감각 오류는 miss + false alarm입니다.
6. 양쪽 오류가 모두 0~2이면 N+1, 어느 한쪽이라도 6개 이상이면 N-1, 나머지는 유지합니다. 최소 N=1이며 상한은 두지 않았습니다. 시작 N은 매 실행 2입니다.

프레임 지연은 기록하지만 사후에 실제 제시가 완벽했다고 보정하지 않습니다. `onset`, `offset`은 블록 첫 flip 기준의 소프트웨어 시각이고 `audio_scheduled_ptb`는 별도의 PTB 시계에 기록한 **예약 시각**입니다. 서로 다른 시계의 값을 바로 빼면 안 됩니다. 이 기록은 물리적 화면·음성 onset 측정값이 아닙니다.

### Digit Span

- 영어 숫자 WAV를 1초 간격으로 예약 재생합니다. 숫자는 1~9이며 바로 인접한 반복을 금지합니다.
- Forward 3~9, Backward 2~8, 길이마다 2회입니다. 같은 길이에서 2회 모두 실패하면 해당 방향의 본검사를 종료합니다.
- 방향별 연습은 최단 길이 2회이며 정답 피드백을 제공합니다. 본검사에서는 정답을 보여주지 않습니다.
- 마지막 숫자의 1초 슬롯이 끝난 뒤 숫자 키로 입력하고 Enter로 제출합니다. Backspace로 수정할 수 있고, 입력 길이를 강제하지 않아 누락·과다 응답도 기록됩니다.
- `exact_serial_accuracy`: 완전히 맞은 시행 수 / 시행 수. `total_correct`: 완전히 맞은 시행 수. `maximum_span`: 한 번 이상 완전히 회상한 가장 긴 길이, 없으면 0입니다.
- 기본 seed는 익명 participant ID에서 안정적으로 계산됩니다. 같은 ID와 같은 설정을 유지하면 Pre/Post 및 두 방향·연습 사이에 동일 숫자 시퀀스를 재사용하지 않습니다. `--seed`를 직접 지정한다면 Pre/Post에서 같은 값을 사용해야 이 보장이 유지됩니다. 설정 변경 후 수집한 자료는 같은 검사 버전으로 간주하지 마세요.

### Reading Span

- Pretest=A, Posttest=B입니다. 각 form은 2·3·4·5문장 세트를 크기별 3개씩, 총 12세트·42문장으로 구성합니다. 연습은 별도 P form의 2문장×3세트입니다.
- 본검사에서는 **세트 순서만 무작위화**하고 세트 안의 문장 순서는 CSV의 `item_order`를 따릅니다. form 전체 True/False가 21/21이며, 연습은 3/3입니다.
- Y=True, N=False로 문장이 말이 되는지 판단하며 마지막 **단어**을 기억합니다. 키는 config에서 변경할 수 있습니다. 영어 초안의 `recall_word`는 문장 끝 문장부호를 제외한 마지막 단어입니다.
- 연습 문장의 판단은 시간 제한이 없습니다. 최신 연습 수행에서 **정답 판단한 문장의 RT만** 사용하여 `평균 + 2.5 × 표본 SD(ddof=1)`를 계산합니다. 유효 RT가 2개 미만이면 연습을 다시 합니다. SD=0도 그대로 적용합니다.
- 본검사에서 무응답 timeout은 처리 오답으로 기록합니다. 모든 세트를 진행하며 조기 중단하지 않습니다.
- 세트가 끝나면 입력창에 단어를 공백으로 구분하여 순서대로 입력합니다. 기억나지 않는 위치에는 `_`를 입력하여 뒤의 단어 위치를 보존합니다. 키보드로 여러 단어를 입력하기 위해 PsychoPy GUI 입력창(Qt/wx)을 사용합니다.
- `processing_accuracy`: 정답 의미 판단 수 / 제시 문장 수. **85% 미만**이면 `processing_below_threshold=True`입니다. 자동으로 참가자를 제외하지 않습니다.
- `position_correct_partial_credit`: 각 세트의 위치 정답 비율을 구한 뒤 세트 간 평균을 냅니다. 길이에 따른 가중 차이를 확인하도록 `item_accuracy`(전체 위치 정답 수 / 전체 단어 수)도 함께 저장합니다.
- `complete_set_accuracy`: 모든 단어와 길이가 정확한 세트 수 / 세트 수입니다. 단어의 단순 포함 여부가 아니라 **동일 위치**인지 비교합니다. 공백 분리 외의 자동 철자·조사·동의어 보정은 하지 않습니다.
- 회상 RT는 회상 안내 시작부터 제출까지의 총 시간으로, 입력창 표시와 타이핑 시간을 포함합니다. 개별 단어의 기억 검색 시간으로 해석하지 않습니다.

## 문항 CSV 검토 및 승인

`stimuli/reading_sentences.csv`는 Excel에서도 열 수 있는 UTF-8 BOM CSV입니다. `form`, `set_id`, `set_size`, `item_order`, `item_id`, `pair_id`, `sentence`, `answer`, `recall_word`, `reviewed`, `word_count`, `review_notes`를 포함합니다. 문장을 수정하면 `word_count`도 공백으로 구분한 어절 수에 맞게 갱신하세요.

초안의 각 문장이 자연스러운지, True/False 정답이 명확한지, 마지막 단어를 회상하기 적절한지 검토하세요. `pair_id`로 A/B 대응 문장을 비교하고 어휘, 문장 길이, 통사 복잡성, 의미 판단 난이도, 마지막 단어의 빈도·회상 난이도를 맞춰 수정하세요. 현재 False 문항에는 명백히 불가능한 사건이 많으므로, 실제 표본에서 천장효과와 난이도를 점검해야 합니다.

1. 검토·수정한 문항의 `reviewed`를 `yes`로 바꿉니다. 연습 P 문항도 포함합니다.
2. 아래 명령으로 구조를 검증하고 **수정이 끝난 CSV의 SHA256**을 확인합니다.

```bash
python3 tools/validate_materials.py --draft
```

3. A/B 난이도 대응 검토를 마친 뒤 `stimuli/reading_review.json`에 `reviewer`를 적고, `forms_difficulty_reviewed`를 `true`, `approved_csv_sha256`를 출력된 해시로 설정합니다.
4. `python3 tools/validate_materials.py`가 통과하는지 확인합니다. CSV가 이후 변경되면 해시가 달라져 다시 검토 상태를 확인해야 합니다.

이 승인은 연구자의 문항 검토 기록입니다. 파일의 `yes` 표시나 해시가 통계적인 동등성 검증을 대신하지 않습니다. **제공된 파일은 모두 `reviewed=no`, 난이도 검토=false입니다.**

## 데이터 파일

세션마다 고유 이름으로 `data/`에 다음 파일을 만듭니다. 참가자 이름은 파일명에 사용하지 않습니다.

- `*_session.csv`: 참가자 ID, 과제, phase, seed, Python/PsychoPy 버전, 설정 스냅샷.
- `*_trial.csv`: N-back 자극·target 여부·실제 flip 시각·키와 RT·감각별 정오·N·블록. `scored=False`인 준비/미완료 시행은 분석에서 구분합니다.
- `*_digit_trial.csv`, `*_digit_summary.csv`: 숫자 원순서·정답순서·응답·입력 키·RT·정확도·방향·길이·점수.
- `*_sentence_judgment.csv`, `*_reading_recall.csv`, `*_reading_summary.csv`: 문장과 정답, 응답, RT, timeout, 단어 위치 채점, 처리 정확도 및 85% 기준 flag.
- `*_reading_timeout.csv`, `*_reading_order.csv`: 제한시간 계산 근거 RT와 실제 세트 순서.
- `*_frame_intervals.csv`, `*_block_summary.csv`, `*_session_end.csv`: 타이밍, 적응 결과, 완료/중단/오류 상태.
- 같은 세션의 `.jsonl`: CSV와 같은 원자료를 보존하는 구조화 로그. 리스트는 CSV 셀 내부의 JSON 문자열로 저장합니다. 추가 필드는 `extra_json`에 보존됩니다.

Span 시행·요약에는 `stage=practice/test`가 들어갑니다. 연습과 본검사 점수를 섞지 마세요. 숫자 RT는 회상 화면 기준, 문장 RT는 문장 화면 기준입니다. 진행 중 중단된 Span 시행은 `*_start.csv`와 `session_end`로 식별되며 완성된 응답처럼 채점하지 않습니다. 저장된 행은 즉시 flush합니다. N-back의 시행별 행은 화면 타이밍에 디스크 쓰기가 영향을 주지 않도록 **블록 종료 또는 ESC 중단 시** 저장하므로, 강제 프로세스 종료 시 해당 블록의 미저장 반응은 유실될 수 있습니다.

## 오디오와 자극

- `stimuli/audio/{B,F,H,J,M,Q,R,W}.wav`: 48 kHz, mono PCM16, 500ms.
- `stimuli/audio/digits/{1..9}.wav`: 같은 형식, 950ms 파일. 자극 시작 간격은 1초입니다.
- `stimuli/audio/manifest.json`: 합성 목소리, 속도, 원래 길이와 시간축 압축 여부.
- `tools/generate_audio.py`: `config.py`의 `AUDIO_GENERATION` 설정과 macOS `say`와 `afconvert`로 파일을 다시 만드는 도구.

합성음은 Samantha 영어 목소리로 만들었습니다. 선행/후행 무음을 정리하고 길이를 넘는 자음은 전체 파형을 시간축 재표본화하여 500ms 안에 맞췄습니다. 이 과정은 음높이·명료도에 영향을 줄 수 있습니다. 원논문의 음성 녹음과 동일하지 않으며, 청취와 판별 가능성 검토가 필요합니다. 실제 녹음으로 교체할 때 파일명과 PCM 형식을 유지하고 `manifest.json`과 실험 버전을 갱신하세요. 사각형은 코드로 생성하므로 별도 그림 파일이 필요하지 않습니다.

## Reproduction assumptions 및 비교 체크리스트

| 항목 | 원문 또는 사용자 명세 | 구현·구분 |
|---|---|---|
| 위치·자음 수 | 원문: 각각 8개 | 구현. 위치는 중심을 제외한 3×3 배열 |
| 제시·ISI | 원문: 500ms / 2,500ms | 프레임 양자화하여 구현, 실제 간격 별도 기록 |
| 반응 키 | 원문: 시각 A / 청각 L | 구현, 비일치 무반응·동시 target 두 키 |
| 시행·블록 수 | 원문: 20+N / 세션 20블록 | 구현 |
| target | 원문: 감각별 6, 중복 2 | 생성 후 실제 일치까지 단위 테스트 |
| N 증가 | 원문: 감각별 오류 3 미만 | 양쪽 모두 2개 이하일 때 증가 |
| N 감소 | 원문: 오류 5 초과, 감각 결합 방식 불명확 | 사용자 승인 가정: 어느 한쪽 6개 이상 |
| 시작·최소 N | 본문 미명시 | 사용자 승인 가정: 2 / 1; 세션 간 자동 승계 없음 |
| 응답·준비 시행 | 상세 기준 미명시 | 사용자 승인 가정: 전체 3초, 첫 N개 적응 채점 제외 |
| 음성·자음 목록 | 정확한 녹음·목록 본문 미명시 | 승인 가정: B F H J M Q R W, 영어 합성음 |
| 화면 외형 | 픽셀 크기·색·거리 미명시 | 기술적 재현 설정: config에서 변경 |
| 오류 정의·반복 키 | 상세 처리 미명시 | miss+false alarm; 감각별 1회 채점, 반복 원자료 보존 |
| 피드백·휴식 | 세부 운영 미명시 | 블록 뒤 오류·다음 N 표시, SPACE로 진행 |
| Digit Span | 원문은 Pre/Post 사용과 참고문헌 제시 | 세부 절차 전체는 사용자 지정 reproduction assumptions |
| Reading Span | 원문은 Pre/Post 사용, 8일 집단에서는 미실시 | 사용자 지정 절차, 영어 미검토 A/B 초안 |
| 연습 | 원문 상세 미명시 | 승인 가정: 숫자 방향별 2회, 읽기 2문장×3세트 |
| 제한시간 산출 | 원문 상세 미명시 | 승인 가정: 정답 연습 RT, 표본 SD, 2개 미만 재연습 |
| Pre/Post 자료 | 구체 Span 문항 미제공 | 숫자 비중복 시퀀스·Reading A/B 분리; 난이도 동등성 미검증 |
| 검사 해석 | 원본 표준화 검사와 동일성 미확인 | WAIS/원본 Reading Span 완전 복제라고 표시하지 않음 |
| 전체 연구 | 원문: 여러 훈련 기간과 Gf 전이 검사 | 본 프로젝트는 요청한 과제 틀. 집단 배정·훈련 일정·RAPM/BOMAT는 구현 범위 밖 |

## 테스트와 검증 범위

PsychoPy가 없는 일반 Python에서도 핵심 테스트가 실행됩니다.

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
python3 tools/validate_materials.py --draft
```

`tools/smoke_psychopy.py`는 한 블록의 실제 화면·음성을 자동 실행하고 입력 대기를 넘깁니다. 기본은 ISI를 짧게 한 기술 검사이며, `--full-timing`을 붙이면 500ms/2,500ms 조건입니다. `tools/smoke_digit.py`는 두 방향의 숫자를 실제 재생하되 회상 답을 자동 오답으로 대체하여 중단 규칙까지 실행합니다. 이 결과는 `data/smoke/`에 저장하며 연구 자료로 사용하지 않습니다.

검증 결과와 한계는 `VALIDATION.md`에 기록했습니다. 자동 검사에서 정상 실행되었다는 사실은 키보드의 실제 사람 반응, 영어 단어 입력, 음성의 청각적 명료도, 20블록 전체의 안정성, 물리적 시청각 동기의 검증을 뜻하지 않습니다.

## 근거 자료

- 사용자 첨부 Jaeggi et al. (2008), *Improving fluid intelligence with training on working memory*, pp. 6829–6833, 특히 p. 6832 Materials and Methods. DOI: [10.1073/pnas.0801268105](https://doi.org/10.1073/pnas.0801268105). [공개 본문](https://pmc.ncbi.nlm.nih.gov/articles/PMC2383929/)
- [PsychoPy 공식 설치 안내](https://psychopy.org/download.html)
- [PsychoPy 음성 예약 재생 안내](https://psychopy.org/api/sound/playback.html)

GitHub 연결로 관련 PsychoPy N-back 저장소를 검색했으나 타 저장소의 코드를 복사하거나 변형해 포함하지 않았습니다. 구현 근거는 첨부 원문, 사용자 지정 절차, PsychoPy API입니다. 기존 상위 폴더의 `nback.py`는 수정하지 않았습니다.
