# 검증 기록 — 2026-10-27

## 최신 변경: 한국시간 기록 v15

- 새 CSV는 `recorded_utc` 대신 `recorded_kst`를 `YYYY-MM-DD HH:MM:SS` 24시간제로 저장합니다. `session_id`와 파일명도 KST `YYYY-MM-DD_HH-MM-SS`를 사용하며 충돌 방지 고유번호는 유지합니다. 기존 UTC CSV는 수정하지 않습니다.
- 이전 완료 Pretest를 찾는 코드는 새 KST와 기존 UTC 기록을 모두 실제 시각으로 비교합니다. 단위 테스트 50개, compileall, diff 공백 검사 통과. 생성된 CSV의 시각·세션 ID 형식과 현재 KST 시각의 일치를 확인했습니다.

## 최신 변경: 사용자 선택 단계 전환 v14

- 선택한 Span Pretest 뒤 Dual N-back Training, Training 뒤 같은 Span Posttest를 제안합니다. SPACE로 계속하고 N으로 멈춥니다. Training을 단독 시작한 경우 같은 이메일의 가장 최근 완료 Pretest를 찾고, 없으면 D/R 키로 Posttest 검사를 고릅니다. 단계마다 독립 CSV·session ID가 만들어지고 참가자 이메일은 유지됩니다. 중단·오류가 난 과제 뒤에는 다음 단계를 제안하지 않습니다.
- 단위 테스트 50개 통과. 세 단계 연속 실행, 단독 Training 뒤 Posttest 선택, 기존 CSV에서 완료된 Pretest 복원, N/SPACE 키 처리를 검사했습니다. 설치된 PsychoPy 2026.2.4에서 전환 제안 화면을 실제 렌더링하고 N 키 종료 경로를 확인했습니다. 자동화된 과제 내부 실행과 실제 사람의 전체 연속 세션은 별도 검증 대상입니다.

## 최신 변경: 시작 과제·단계 선택 재시도 v13

- `Digit Span/Reading Span + Training` 또는 `Dual N-back + Pretest/Posttest`를 선택하면 예외로 종료하지 않고 경고창을 띄운 뒤 선택 창을 다시 엽니다. 이전 선택을 유지한 채 드롭다운의 전체 선택지가 다시 표시됩니다. 이메일 형식 오류도 같은 선택 창으로 돌아갑니다. 유효한 선택을 마친 뒤에만 DataLogger와 실험 창을 만듭니다.
- 단위 테스트 45개 통과. 잘못된 조합 후 `Digit Span + Pretest`로 고쳐 실행되는 흐름, 두 번째 드롭다운 선택지, 최종 CSV 하나 생성, Dual N-back의 Training 조건을 확인했습니다. 실제 사람의 GUI 클릭은 자동화하지 않았습니다.

## 최신 변경: 사용자 제공 Reading Span 문장 예시

- Form A의 `A09/A35/A25/A03/A07/A37`, Form B의 대응 `B09/B35/B25/B03/B07/B37`에 제공된 문장과 마지막 회상 단어를 순서대로 입력했습니다. 모두 기존 True 문항이어서 Form별 21 True / 21 False와 2~5문장 세트 구조를 유지합니다. `word_count`를 다시 계산하고 `reviewed=no`를 유지했습니다. 각 Form의 나머지 36문장과 연습 6문장은 기존 초안입니다.
- 문항 구조 검사와 단위 테스트 43개가 통과했습니다. 수정 후 CSV SHA256은 `900c93f18a47cb9288cae295974cce10e0f7a926f15a238b3da807db1d5e2f21`입니다. 제공된 문장의 길이·단어 빈도·회상 난이도 및 A/B 동등성은 아직 사전 검토가 필요합니다.
- 설치된 PsychoPy 2026.2.4에서 자동 키 응답과 모의 단어 회상으로 Pretest(Form A)와 Posttest(Form B)를 각각 끝까지 실행했습니다. 두 실행 모두 수정된 문항을 포함한 본검사 42문장과 총 63개의 행동 행을 저장했고, 모든 행에 `material_status=draft`가 기록됐습니다. 사람의 실제 입력·문항 이해도는 확인하지 않았습니다.

## 최신 변경: Reading Span 초안 개발 실행 v12

- 보고된 중단 지점은 `utils/span_protocol.py:124`의 `Unreviewed item: A18`입니다. 제공된 CSV 90문항의 `reviewed=no`와 승인 파일의 빈 reviewer/hash로 인해 기존 정식 실행 차단이 작동한 것이었습니다.
- `READING_SPAN.allow_draft_materials=True`인 개발 상태에서는 문항의 형식·세트 구조는 검사하면서 승인 문턱만 건너뛰어 과제를 실행합니다. 화면에 `DRAFT MATERIALS`를 알리고 반응 CSV에 `material_status=draft`를 남깁니다. `False`로 바꾸면 개별 문항 승인과 A/B 검토 해시가 다시 필요합니다.
- 단위 테스트 43개와 문항 초안 구조 검사, compileall, diff 공백 검사가 통과했습니다. 설치된 PsychoPy 2026.2.4로 화면을 실제 그리며 자동 응답 Pretest를 끝까지 실행했고, 임시 단일 CSV의 63개 반응 행이 모두 `material_status=draft`, `session_status=completed`였습니다. 이 자동 검사는 실제 사람의 문장 판단·회상 또는 문항 난이도를 검증하지 않습니다.

## 최신 변경: Forward 고정과 시작 대기 문구 v11

- 참가자용 시작 입력창의 Forward/Backward 선택란과 CLI `--mode`를 제거했습니다. Digit Span을 시작하면 `forward`가 과제 호출과 기록에 전달됩니다. 내부 Backward 함수는 기존 핵심 알고리즘 검증을 위해 보존했습니다.
- PsychoPy 창 생성 중 주사율 측정 화면의 기본 `Attempting to measure frame rate...` 문구를 `Waiting...`으로 바꿨습니다. 주사율 측정 자체는 유지합니다.

## 최신 변경: 무응답 피드백 숨김 v10

- 이전 요청의 시작 창 `fullscreen` 체크박스 제거와 macOS 기본 전체화면 버튼 활성화도 현재 작업본에 반영했습니다. Cocoa 창의 크기 조절·전체화면 스타일을 켜고 Retina framebuffer/viewport를 크기 변경에 맞춰 갱신합니다.
- 시행 중에는 실제 A/L 키 입력의 결과만 표시합니다. 키를 누르지 않은 감각은 시행이 끝난 뒤에도 `Correct` / `Incorrect`를 화면에 표시하지 않습니다. RT=2.99초의 유효한 입력도 해당 시행의 hit로 채점합니다. 다만 바로 다음 화면 갱신이 새 시행 시작과 겹치면 그 입력의 피드백은 화면에 나타나지 않을 수 있어도, 반응·RT·정오답 기록에는 반영됩니다.
- 무응답은 3초 응답 기한 이후 `miss` 또는 `correct_rejection`으로 확정합니다. 블록 오류·정답 수·정확도·다음 N, CSV의 시행별 `outcome`·`correct`·블록 통계에는 그대로 반영합니다. 마지막 시행 뒤의 무응답 표시 대기 시간도 제거했습니다.
- 단위 테스트 41개, compileall, `git diff --check` 통과. PsychoPy 2026.2.4에서 단축 ISI·자동 입력 1블록을 완료했습니다(`data/smoke/dual_nback_20261027T060811_9c6fbe39_responses.csv`). 청각 무응답 20개 중 target miss 6개, non-target correct rejection 14개가 저장됐고, 블록 청각 오류 6개·다음 N=1과 일치했습니다. 사람 입력과 원래 2,500ms ISI를 검증한 결과는 아닙니다.

## 최신 변경: 무응답 표시와 블록별 N 재확인 v9

- 시각·청각 각 감각에서 응답하지 않은 시행을 3초 기한 뒤 채점해, 다음 시행 첫 0.75초에 하단 박스에 `Correct` 또는 `Incorrect`로 표시합니다. 박스 제목은 항상 `Visual` / `Auditory`로 유지합니다. 현재 시행의 키 반응은 같은 박스에서 우선 표시됩니다. 마지막 시행의 무응답은 블록 요약 직전 0.75초에 표시합니다. 시행별 사각형·음성 간격을 늘리지 않습니다.
- 블록 종료 후 시각·청각 오류가 모두 0~2개면 N+1, 하나라도 6개 이상이면 N−1(최소 1), 나머지는 N 유지입니다. 감소 조건은 `decrease_rule="either"`라는 재현 가정입니다. 블록 요약에 `Current N → Next N`을 보여 주고, 실제 다음 블록의 생성·상단 N 표시·CSV `n`/`next_n`에 반영합니다.
- 일반 Python의 단위 테스트 40개, 전체 소스 compileall, `git diff --check`가 통과했습니다. 설치된 PsychoPy 2026.2.4로 단축 ISI(100ms)·자동 입력 2블록을 완료했습니다. `data/smoke/dual_nback_20261027T054629_b75e8ea1_responses.csv` 한 파일에 43시행이 저장됐습니다. 첫 블록 N=2, 시각 오류 14·청각 오류 6, `next_n=1`; 두 번째 블록은 N=1로 실제 실행됐습니다. 이 검사는 시각·청각 물리적 동기나 사람의 반응을 측정한 결과가 아닙니다.

## 최신 변경: Hanyang email v8

- PsychoPy Coder 시작 설정 창의 `email` 필드에 한양대학교 이메일을 입력하도록 변경했습니다. 공식 안내의 `통합ID@hanyang.ac.kr` 형식을 확인하고, 공백 제거·소문자 정규화·도메인 검사 후 이를 `participant`로 사용합니다. CLI는 `--email`을 지원하며 이전 `--participant` 인수도 이메일을 입력했을 때만 허용합니다. 형식이 틀리면 대화창에서 다시 입력할 수 있습니다.
- 정규화한 이메일이 모든 시행 CSV 행의 `participant`에 들어가며, Span의 Pre/Post 기본 seed도 동일 이메일을 기준으로 계산합니다. 파일명에는 이메일을 사용하지 않습니다. 계정 비밀번호·학교 SSO 검증은 구현하지 않았습니다.
- **38개 단위 테스트 통과**. 유효 이메일 정규화, 잘못된 도메인/누락/비정상 주소 거부, GUI 입력→실행→단일 CSV 참가자 열 전달을 모의 PsychoPy로 확인했습니다. 실제 학교 계정의 소유자 확인, 실제 사람의 GUI 입력, 학교 SSO 동작은 검증하지 않았습니다. 이전 PsychoPy 자극 기술 검사의 결과는 별도 기록을 참고하세요.

아래는 이전 버전의 검증 이력입니다.

## 이전 변경: Behavior CSV v7

- 사용자 요청 명확화: 파일 수를 줄이되 개별 반응 원자료·RT·재채점 가능성은 보존해야 합니다. 직전 요약 전용 저장 변경은 철회하고, 매 실행 `*_responses.csv` 한 파일에 참가자 행동만 저장하도록 변경했습니다. 기존 파일은 삭제·변환하지 않았습니다.
- N-back의 한 행은 한 시행입니다. 참가자·블록·N, 실제 위치와 알파벳, target, 반응 키·창, 감각별 최초 RT·반응 여부·정오답·outcome, 반복·동시 키 목록과 개별 RT·최초 반응 flag, 준비/채점/완료 여부, 시각 onset/offset을 보존합니다. 블록 정확도와 다음 N도 동일한 시행 행의 열로 저장합니다. 장치·시스템·프레임별 진단 목록은 제외하며 별도 session/block summary/JSONL 파일은 생성하지 않습니다.
- 중단된 N-back 시행은 현재까지 수집된 반응과 자극을 보존하고 미완료·미채점으로 표시합니다. 확정할 수 없는 정오답은 빈칸입니다. 완료한 시행의 무응답은 RT 빈칸·responded=false와 miss/correct_rejection으로 구분합니다. 세션 종료 상태는 같은 파일의 각 행에 반영합니다. 진행 중 블록의 강제 프로세스 종료 복구는 지원하지 않습니다.
- Digit Span·Reading Span도 동일한 단일 CSV 정책으로 개별 자극·응답·RT·점수를 보존합니다. 숫자 키 이벤트와 최종 단어 응답은 CSV 셀의 구조화 값으로 저장합니다. Reading Span 미승인 문항을 실제 참가자 검사로 실행하지 않았습니다.
- **35개 단위 테스트 통과**, compileall·diff 공백 검사 통과. 단일 파일 외 생성 차단, 반복/동시 반응·RT 유지, 무응답/준비/중단 구분, block 정확도, Span 응답과 중단 자극, Unicode·CSV 인용부호, 기존 파일 미덮어쓰기 검증을 포함합니다.
- 실제 PsychoPy 2026.2.4 단축 기술 검사(500ms 제시/100ms ISI)의 **22시행 한 블록 완료**. 출력: `data/smoke/dual_nback_20261027T053023_f78b33d6_responses.csv`. 같은 실행 prefix의 파일은 이 CSV **한 개뿐**임을 확인했습니다. 22행·20개 채점 행·completed 상태를 확인하고, 저장된 키와 RT로 재계산한 최초 RT와 감각별 outcome, 블록 정확도가 모두 일치함을 확인했습니다. 이는 원래 500ms/2,500ms 타이밍의 새 측정값이 아닙니다.
- 실제 사람 입력, 전체 20블록, 물리적 시청각 동기, Span의 사람 전체 수행은 이번에 직접 검증하지 않았습니다. 저장 정책 외 시행·적응 규칙은 유지합니다.

재검사: `python3 -m unittest discover -s tests -v`.
단일 CSV 실제 실행: `python tools/smoke_psychopy.py --scripted-responses --audio-skip-check`.

아래는 이전 버전의 검증 이력입니다. 기존 버전의 JSONL·여러 CSV 설명은 현재 저장 정책에 해당하지 않습니다.

## 이전 변경: Sharp display v5

- 프로토콜 `2026-10-27-sharp-display-v5`. 시행 사이 `Previous trial` 문구를 제거했습니다. 현재 키 반응의 정오답만 표시하며 무응답 정오는 로그로 보존합니다. 기존 `result_display_onset`은 호환성을 위해 null로 유지합니다.
- A/L 박스 중심 y를 -0.405로 이동했습니다. 기본 자극의 최하단 y=-0.280과 박스 상단 y=-0.335 사이에 0.055 height 간격이 있습니다. 아래 중앙 자극이 나타나는 실제 렌더링을 창 모드·전체 화면에서 확인했습니다. 위치는 `NBACK_UI`에서 조정합니다.
- Visual/Auditory별 정답·오답 수·정확도를 블록 요약에 표시하고 `block_summary.statistics`에 기록합니다. 기본 분모는 준비 시행을 제외한 20개이며 hit와 correct rejection을 모두 정답에 포함합니다. 준비 시행 채점을 켠 경우 실제 채점 완료 개수를 분모로 사용합니다.
- 시작 설정 창에 `fullscreen` 체크박스, CLI에 `--fullscreen` / `--windowed`를 추가했습니다. 세션 설정에 실제 선택을 보존하고 `display_runtime`에 framebuffer 크기·Retina 사용 여부를 기록합니다. 실행 중 전환은 지원하지 않습니다. 전체 화면에서는 PsychoPy가 현재 화면 크기를 사용합니다.
- Dual N-back은 시스템 Helvetica TrueType을 Pillow로 두 배 해상도에서 그린 뒤 실제 framebuffer 크기로 축소해 표시합니다. `useRetina=True`를 명시하고 이미지 확대를 하지 않습니다. 시행 헤더·피드백·고정점은 시행 전에 텍스처를 생성하며 재사용합니다. `stimuli/text.py`가 렌더링과 제한된 캐시를 담당합니다. 폰트 경로는 `config.py`에서 변경합니다. 실제 디스플레이 배율과 물리적 해상도에 따른 차이는 남습니다.
- **31개 단위 테스트 통과**. 새 정확도 검사는 감각별 18/20=90%, 15/20=75%, 0%, 준비 시행 포함 분모, 잘못된 오류 개수를 확인합니다. 기존 응답·채점·일정 검사에서 이전 시행 문구가 나타나지 않는 것도 확인합니다. compileall·diff 공백 검사 통과.
- 실제 PsychoPy 2026.2.4로 `data/smoke/ui_v5/`와 `data/smoke/ui_v5_fullscreen/` 화면을 캡처했습니다. 창 모드의 하단 자극·피드백, 요약 지표·배치를 육안 확인했으며 전체 화면의 하단 자극·피드백도 확인했습니다. 전체 화면은 OS가 보고한 2240×1260 크기를 선택했습니다.
- 창 모드의 500ms/2,500ms **22시행 한 블록 완료**: `data/smoke/dual_nback_20261027T052022_9ee6fae4.jsonl`. 소프트웨어 기록은 사각형 499.551~501.299ms(평균 500.025ms), onset 간격 2,999.575~3,000.299ms(평균 2,999.951ms), 지연 프레임 0개입니다. 음성 22개 모두 PTB StartTime을 기록했습니다. 요약 통계가 준비 시행을 제외한 시행별 outcomes와 일치하고, 이전 결과 표시 시각이 모두 null임을 확인했습니다. 자동 주입 키를 사용했으며 실제 사람 반응이나 물리적 시청각 동기를 검증한 수치는 아닙니다.
- 전체 화면 원래 간격의 기술 실행은 진행 중 ESC로 중단됐습니다(`dual_nback_20261027T051854_09aeb61e.jsonl`). 완료한 블록으로 해석하지 않습니다. 이후 창 모드에서 별도로 원래 간격의 블록을 검사했습니다. 전체 화면 20블록, 사람의 키 반응, 물리적 시청각 동기는 검증하지 않았습니다.

재검사: `python3 -m unittest discover -s tests -v`.
화면 캡처: `python tools/preview_nback_ui.py [--fullscreen]`.
원래 간격 자동 검사: `python tools/smoke_psychopy.py --full-timing --scripted-responses [--fullscreen]`.

아래는 이전 버전의 검증 이력입니다.

## 이전 변경: White flow v4

- 프로토콜 `2026-10-27-white-flow-v4`. 안내·소리 확인·준비·휴식 화면을 흰색으로 통일하고, 짙은 회색 상단 띠에 큰 흰색 `DUAL-N-BACK` 제목을 표시했습니다. 단계마다 여정 목록 / 큰 알파벳과 진행 표시 / A·L 키 안내 / 자극 주기 도식을 사용합니다. 하단은 클릭 기능 없는 키보드 버튼 모양입니다. 실제 시행 화면의 남색 배경·푸른 사각형은 유지합니다.
- 재생 중 SPACE: 현재·예약 음성을 멈추고 다음 안내로 이동하며 `audio_check`에 `confirmed=false`, `skipped=true`, `reason=participant_space`를 기록합니다. 전체 재생 후 확인과 구분합니다. 블록 끝의 `Last: Visual ... | Auditory ...` 표시는 제거했습니다. 원자료의 정오·RT는 유지합니다.
- 블록 사이 휴식은 첫 휴식 화면 flip부터 실제 시계로 10초를 측정합니다. SPACE 없이 자동 진행하고 ESC 중단은 유지합니다. 첫 블록에만 3초 준비를 적용하며, 마지막 블록은 완료 화면입니다. 휴식 설정과 실제 경과 시간은 `block_rest` 이벤트로 기록됩니다. 10초 휴식은 사용자 지정 재현 조건이며 논문 명시 조건이 아닙니다.
- **29개 단위 테스트 통과**, compileall 및 diff 공백 검사 통과. 새 동작 검사: 소리 재생 중 SPACE 시 나머지 음성 미예약·정지·미확인 기록, ESC 시 음성 정지, 휴식의 10초 측정·자동 진행·ESC 중단·SPACE로 단축하지 않음.
- 실제 PsychoPy 2026.2.4에서 소리 확인 SPACE를 주입하고 짧은 ISI의 2블록 실행을 완료했습니다. 로그: `data/smoke/dual_nback_20261027T045110_c6a61586.jsonl`. 첫 음성을 예약한 시점의 건너뛰기가 기록됐고 두 번째 블록까지 completed입니다. 휴식의 실제 기록은 **10.033초**입니다. 화면 갱신과 처리 시간 때문에 명목 10초와 수십 ms 차이가 있을 수 있습니다. 단축 기술 검사이므로 이 로그를 원래 500ms/2,500ms 타이밍 검증으로 해석하지 않습니다.
- 최종 안내·청취·응답·속도·준비·휴식·종료·시행 화면은 `data/smoke/ui_v4/`에 실제 렌더링했습니다. 시작·청취·응답·속도·휴식 화면의 가독성과 배치를 육안 확인했습니다.
- 실행 중 기존 macOS 입력기/pyglet의 `insertText_` 빈 문자열 IndexError 콜백 경고가 출력됐지만 자동 검사는 완료됐습니다. 실제 사람의 SPACE/A/L 및 동시 키, 발음 명료도, 출력 장치 변경·재청취 사람 조작, 전체 20블록과 물리적 시청각 동기는 이번에 직접 검증하지 않았습니다.

재검사: `python3 -m unittest discover -s tests -v`.
PsychoPy 기술 검사: `python tools/smoke_psychopy.py --blocks 2 --scripted-responses --audio-skip-check`.
화면 캡처: `python tools/preview_nback_ui.py`.

아래는 이전 버전의 검증 이력입니다.

## 이전 변경: Participant UI v3

- 프로토콜 버전 `2026-10-27-participant-ui-v3`. 단계별 안내, 속도 예고, 블록 전 3초 카운트다운, 남색 배경·푸른 사각형, 상시 N/블록/시행 표시, 큰 `Correct`/`Incorrect` 피드백으로 수정했습니다. UI 변경과 준비 시간은 사용자 요청에 따른 재현 가정으로 구분하며 세션 메타데이터에 저장합니다.
- **26개 단위 테스트 통과**, Python 소스 compileall 통과. 기존 응답 창, 경계 입력 배정, 반복 키, 감각별 채점·적응, 피드백에 따른 시행 일정 불변 검사를 유지했습니다. 피드백 기대 문자열만 간략한 문구에 맞췄습니다.
- macOS Samantha TTS 입력을 대문자에서 `bee / eff / aitch / jay / em / cue / ar / double you`로 바꾸고 **8개 WAV를 실제 재생성**했습니다. manifest와 설정의 일치를 확인했습니다. 모두 mono PCM16 / 48kHz / 500ms이며 이번 합성음에는 시간축 압축이 없습니다. 숫자 WAV는 기존과 동일합니다. 음성 파형·길이 검증은 사람이 듣는 발음 검증과 구분합니다.
- 설치된 PsychoPy **2026.2.4 / 내장 Python 3.11**로 실제 UI를 렌더링했습니다. 시작, 응답 방법, 속도 예고, 소리 확인, 카운트다운, 시행 피드백, 휴식 화면을 `data/smoke/ui_v3/`에 캡처했습니다. 시작·응답·속도·시행·휴식 화면을 육안 확인하고, 단계 강조 색상이 화면 전환 때 갱신되도록 수정한 뒤 다시 캡처했습니다.
- 500ms/2,500ms 조건으로 N=2 **22시행 한 블록 자동 실행 통과**. 로그: `data/smoke/dual_nback_20261027T042109_96841eff.jsonl`. 응답은 기술 검사 스크립트가 주입했습니다. 22개 음성 모두 PTB StartTime이 기록됐고 세션 completed가 저장됐습니다. 실제 선택 출력은 iMac 스피커입니다.
- 소프트웨어 flip 기록: 사각형 **499.848~500.124ms (평균 499.968ms)**, 연속 onset 간격 **2,999.886~3,033.364ms (평균 3,001.606ms)**, 지연 프레임 1개. 모니터 교정 프로필 없음 경고와 기본 스피커 자동 선택 경고가 있었습니다. 물리적 AV 동기 측정값이 아닙니다.
- 자동 블록에서는 사람의 청취 확인을 건너뛰었습니다. **실제 발음 명료도·헤드폰 음량, A/L 실제 동시 입력, 출력 장치 변경 및 replay의 사람 조작, 전체 20블록 세션은 이번에 직접 검증하지 않았습니다.** 참가자 실험은 기본 청취 확인을 유지합니다.

재검사:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q config.py main.py tasks stimuli utils tools tests
# 아래는 PsychoPy Coder 또는 PsychoPy가 설치된 Python에서 실행
python tools/preview_nback_ui.py
python tools/smoke_psychopy.py --full-timing --scripted-responses --preview
```

아래는 이전 버전의 검증 이력입니다.

## 최신 변경: English feedback v2

- 프로그램 화면·입력창·오류 메시지를 영어로 전환하고 활성 Reading Span CSV를 영어 초안 90개로 교체했습니다. 이전 한국어 자료는 `stimuli/archive/`에 보존했습니다. 모든 영어 문항은 미승인 상태입니다.
- **26개 단위 테스트 통과**. 신규 테스트에서 Hit/Miss/Correct Rejection/False Alarm, 2.7초 반응, 정확히 3초 경계, 다음 프레임에서 늦게 수집한 키의 원래 시행 배정, 반복 입력, 감각별 독립 피드백을 확인합니다.
- 모의 프레임 루프에서 2.7초의 A 입력은 즉시 Correct (Hit) 피드백을 생성하며, 무응답 시행과 비교해 다음 자극 onset이 바뀌지 않습니다. 3초까지 응답하지 않은 감각의 결과는 그 이후에만 표시됩니다.
- 실제 PsychoPy 2026.2.4에서 500ms/2,500ms 조건의 22시행 한 블록을 실행했습니다. 로그: `data/smoke/dual_nback_20261026T075030_294a00bf.jsonl`.
- 공유 PTB 출력 장치에서 **22개 음성 모두 StartTime이 기록**됐고 첫 음성 상태에는 XRuns=0이 기록됐습니다. 기록된 출력은 MacBook Pro Speakers입니다. 물리적 헤드폰 출력이나 실제 귀에 들리는 정도를 측정한 것은 아닙니다.
- 키 입력은 검사 스크립트로 주입했습니다. 이 실행에는 실제 입력 이벤트도 일부 섞였으므로 참가자의 수행 점수로 해석하지 않습니다. 이후 기술 검사 스크립트는 주입 모드에서 ESC를 제외한 실제 입력을 배제하도록 바꿨습니다.
- 영어 피드백 화면을 캡처하여 사각형·중앙 고정점·현재 감각별 정오·이전 시행 결과가 겹치지 않는 것을 확인했습니다: `data/smoke/feedback_preview.png`.
- 실제 제시 시간은 492.382~505.515ms(평균 500.608ms), 연속 onset 간격은 2,991.637~3,033.479ms(평균 3,003.227ms), 지연 프레임은 5개였습니다. OS/화면 지연까지 없다고 보장하지 않습니다. 코드의 프레임 일정은 키 입력과 피드백에 따라 멈추거나 조기 종료되지 않습니다.
- macOS 입력기 처리 중 PsychoPy/pyglet 내부 `insertText_` 콜백에서 빈 문자열 IndexError가 출력됐지만 자동 블록은 완료됐습니다. 실제 실행 전 입력 소스를 **ABC/English**로 선택하고 A/L 입력을 점검하세요. 이 프로젝트에서 외부 라이브러리 코드를 수정하지는 않았습니다.
- 실제 사람이 응답하는 전체 세션, Audio check에서 직접 장치를 전환하는 경로, 물리적 시청각 동기는 아직 직접 검증하지 않았습니다. 시작 전 청취 확인 화면을 추가하여 사용자가 무음을 확인하고 장치를 선택할 수 있도록 했습니다.

재검사(일반 Python): `python3 -m unittest discover -s tests -v`.
실제 PsychoPy 기술 검사: `python tools/smoke_psychopy.py --full-timing --scripted-responses --preview`.
기술 검사는 청취 확인을 건너뛰며, 실제 실험은 기본 `check_before_session=True`를 유지합니다.

## 이전 버전 자동 검사

- Python 표준 `unittest`: **18개 통과**.
- 전체 Python 소스 `compileall`: 통과.
- N-back: N=1,2,3,8,25 × seed 100개 = **500블록**의 실제 일치와 target 6/6/2, 길이 20+N, 준비 시행, 우연한 추가 일치 부재를 확인했습니다.
- 적응 기준: 오류 2/3/5/6 경계, 한 감각만 실패하는 경우, 최소 N을 확인했습니다.
- Digit Span: 25개 seed의 Pre/Post·두 방향·연습/본검사 시퀀스 중복 부재, 인접 반복 금지, 범위, 순서 역전 및 점수를 확인했습니다.
- 모의 입출력 실행: Digit Span 두 번 실패 시 중단 및 전부 정답일 때 최장 길이 도달, Reading Span 모든 본검사 문장에서 timeout되어도 **42문장·12세트 모두 진행**하는 것을 확인했습니다.
- Reading Span: 표본 SD 기반 제한시간, 위치별 채점, 85% 경계, 완전세트 점수, 부분점수의 세트/항목 가중 차이를 확인했습니다.
- 문항: A/B 각 12세트·42문장, P 3세트·6문장, form별 True/False 균형, 마지막 어절, A/B 대응 구조 검증을 통과했습니다. **모든 문항은 미승인**이며 실행 차단도 검증했습니다. 승인 후 CSV 변경 시 해시 검사가 차단하는 것은 임시 fixture에서만 테스트했습니다.
- WAV 17개: 파일 존재, mono PCM16, 48kHz, 길이, 무음이 아닌 표본을 확인했습니다. 이것은 청취 검사가 아닙니다.
- CSV: 한글, 쉼표·따옴표, 중첩 값, stage/phase, 추가 필드 보존, 기존 파일 미덮어쓰기를 검사했습니다.

## 설치된 PsychoPy의 실제 실행

이 컴퓨터의 macOS PsychoPy Standalone **2026.2.4**, 내장 Python **3.10.11**을 사용했습니다. 창 모드에서 PTB가 MacBook Pro Speakers를 선택했습니다. 사람의 실험 응답을 사용하지 않은 기술 검사입니다.

1. 짧은 N-back 검사: ISI 100ms의 자동 블록이 완료됐습니다. 초기 실행에서 2026.2.4가 오디오 백엔드 이름을 소문자 `ptb`로 해석하는 차이를 확인해 수정했습니다.
2. 원래 간격의 N-back 검사: 500ms / 2,500ms, N=2, **22시행의 한 블록**을 완료하고 CSV/JSONL을 저장했습니다. 초기에 짧은 주사율 평균으로 181프레임을 선택하는 문제를 발견하여, 120개 실제 flip 간격의 중앙값을 사용하고 제시/ISI를 각각 환산하도록 수정했습니다.
3. 최종 N-back 실행 파일: `data/smoke/dual_nback_20261026T065836_65308db6.jsonl`.
4. Digit Span Forward/Backward: 실제 음성 파일을 각각 연습 2회+본검사 2회 재생했습니다. 회상 입력을 자동 오답으로 대체하여 같은 길이 두 번 실패 후 종료되는 것을 확인했습니다. 모든 예약 음성 시작 간격은 1.000000초입니다. 실제 스피커 출력 시각은 별도로 측정하지 않았습니다.

최종 N-back 소프트웨어 기록:

| 측정 | 최소 | 평균 | 최대 |
|---|---:|---:|---:|
| 사각형 제시 시간 | 498.272ms | 499.919ms | 500.529ms |
| 연속 시행 시작 간격 | 2,998.842ms | 3,000.849ms | 3,016.878ms |

측정된 주사율은 약 59.927Hz, 제시는 30프레임, ISI는 150프레임, 시행은 180프레임이었습니다. 1.5배 프레임 간격 기준으로 **지연 프레임 4개**가 기록됐습니다. 이 환경에서 모든 시행이 정확히 500/3,000ms였다고 주장할 수 없습니다.

실행 도중 macOS HID 열거 경고 후 일반 입력 장치 일부를 사용하도록 복구되었다는 메시지가 나왔습니다. 실제 A/L 동시 반응 및 키보드 권한은 사람을 통한 사전 점검이 필요합니다. 모니터 교정 프로필이 없어 임시 프로필을 쓴다는 경고도 있었습니다.

## 직접 확인하지 못한 기능

- 사람의 A/L 반응과 동시 키, 숫자 키·Backspace·Enter 입력의 전체 경로.
- Reading Span의 실제 한국어 입력/IME 및 사람의 전체 Pre/Post 수행. 미승인 문항을 승인된 연구 문항처럼 실행하지 않았습니다.
- 20블록 전체 세션, 여러 날에 걸친 연구 운영, 중간 프로세스 강제 종료에서의 데이터 복구.
- 헤드폰에서의 음성 명료도·음량, 화면 크기·시거리의 원연구 동등성.
- 광센서·마이크 등 외부 장치를 통한 물리적 시청각 onset 동기와 키보드 지연.
- Reading A/B의 통계적 난이도 동등성, 표준화 검사 신뢰도/타당도, 원논문의 지능 전이 효과.

## 재실행

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
python3 tools/validate_materials.py --draft
python3 tools/report_timing.py data/smoke/dual_nback_20261026T065836_65308db6.jsonl
```

PsychoPy Coder에서 `tools/smoke_psychopy.py` 또는 `tools/smoke_digit.py`를 실행할 수 있습니다. 원래 N-back 시간 조건은 PsychoPy가 설치된 Python에서 `python tools/smoke_psychopy.py --full-timing`으로 검사하세요. 자동 검사의 데이터는 `data/smoke/`에만 저장됩니다. 자료를 분석할 때 본검사 자료와 섞지 마세요.
