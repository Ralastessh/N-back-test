# Jaeggi (2008) PsychoPy 과제 재현 프로젝트

학부 수준에서 코드를 설명하고 수정할 수 있도록 자극 생성, 제시, 채점, 저장을 나눈 프로젝트입니다. Dual N-back의 명시된 조건은 원문을 따르며, Span 검사는 사용자가 지정한 절차로 구현했습니다. **원본 WAIS 또는 원본 Reading Span 검사를 완전히 복제한 검사가 아닙니다.**

Reading Span의 영어 문장은 **미검토 초안**입니다. A/B 각 42문장과 연습용 6문장이 있으나, 문항 검토 및 A/B 난이도 대응 검토 전에는 실행되지 않습니다. 구조를 맞춘 것이 경험적 난이도 동등성을 입증하지는 않습니다.


## 수정 사항: 한양대학교 이메일로 참가자 구분 (2026-10-27)

현재 실행 코드는 프로젝트 최상위 `main.py`, `tasks/`에 있습니다. `PROTOCOL_VERSION`은 `2026-10-27-omission-feedback-v9`입니다.

- 검사 시작 시 `Hanyang participant sign-in` 창에서 **한양대학교 이메일**을 입력합니다. 공식 계정 형식인 `통합ID@hanyang.ac.kr`만 허용하고 앞뒤 공백·대문자를 정리합니다. 형식이 잘못되면 안내 후 다시 입력합니다. 같은 이메일은 모든 세션에서 같은 `participant` 값으로 저장됩니다. 이것은 입력 주소 형식 검사이며 실제 계정 소유자 인증이나 학교 SSO 연동은 아닙니다.
- 이 이메일을 참가자 식별자와 Span Pre/Post 시퀀스의 안정적인 seed 입력으로 사용합니다. 이메일은 CSV에 직접 저장되며 파일명에는 넣지 않습니다. 지원 도메인은 `config.py`의 `PARTICIPANT_EMAIL_DOMAIN`에서 설정합니다. [한양대학교 IT 서비스의 계정 형식 설명](https://www.hanyang.ac.kr/web/www/it_s?_board_WAR_bbsportlet_action=view_message&_board_WAR_bbsportlet_messageId=699885&login_post_proc=true&p_p_col_count=1&p_p_col_id=column-1&p_p_id=board_WAR_bbsportlet&p_p_lifecycle=0&p_p_mode=view&p_p_state=normal)을 참고했습니다.
- **세션당 `*_responses.csv` 하나만** 생성합니다. 참가자의 시행별 자극·RT·정오답·실제 반응을 보존하며, JSONL·시스템 설정·세션·블록 요약 등의 별도 파일은 생성하지 않습니다. 이전 요약 전용 변경은 철회했습니다. 기존 자료는 수정·삭제하지 않습니다.
- Dual N-back은 한 행이 한 시행입니다. 시각 위치·청각 알파벳·N·target 여부·감각별 RT·정오답, 무응답·반복·동시 반응, 준비/채점/완료 여부를 보존합니다. 블록 정확도도 동일 CSV의 열로 추가하여 개별 RT 분석과 사후 재채점이 가능합니다. 시스템·장치 설정과 프레임별 진단 목록은 제외합니다.
- 시행 중 현재 A/L 키 반응은 해당 박스에 즉시 `Correct` / `Incorrect`로 표시합니다. 아무 키도 누르지 않은 감각은 3초 응답 기한이 지난 뒤 다음 시행 첫 0.75초 동안 같은 박스에 결과를 표시합니다. 불일치 무응답은 `Correct`, 일치 무응답은 `Incorrect`입니다. 마지막 시행의 무응답 결과는 블록 요약 직전에 0.75초 동안 표시합니다. 표시 시간은 `NBACK_FEEDBACK.omission_result_s`에서 바꿀 수 있습니다.
- A/L 피드백 박스 중심을 -0.335에서 **-0.405 height**로 이동했습니다. 기본 크기에서 가장 아래 사각형의 하단(-0.280)과 피드백 상단(-0.335) 사이에는 0.055 height 간격이 있습니다. 위치·박스 높이는 `NBACK_UI.feedback_y`, `feedback_panel_height`에서 조정합니다.
- 블록 요약에 Visual/Auditory 각각 **정답 수·오답 수·정확도**를 표시하고 같은 반응 CSV의 `block_*` 열에 저장합니다. 정확도는 `(hit + correct rejection) / 채점 완료 시행 수`입니다. 기본 설정은 준비 시행 제외 **20개**가 분모이며, 예를 들어 오류 2개면 `Correct 18/20 | Incorrect 2`, `90%`입니다. 화면은 정수 퍼센트로 반올림하고 요약 CSV에는 비율 실수를 저장합니다. 단순 target 검출률과 구분합니다. `score_warmup=True`로 변경하면 실제 채점에 포함된 시행 수를 사용합니다.
- **전체 화면**은 시작 설정 창에서 `fullscreen`을 체크하거나 터미널 명령에 `--fullscreen`을 붙입니다. `--windowed`는 창 모드입니다. 기본값은 `DISPLAY.fullscr`이며 실제 선택·framebuffer 크기는 반응 CSV에 저장하지 않습니다. 실행 도중 전환하는 방식은 지원하지 않습니다.
- Dual N-back 글자는 macOS **Helvetica TrueType**을 실제 framebuffer 픽셀 크기로 렌더링합니다. 2배 해상도에서 윤곽을 그리고 네이티브 해상도로 축소해 표시하며 `useRetina=True`를 명시했습니다. 고해상도 글자 텍스처와 캐시를 담당하는 모듈은 `stimuli/text.py`입니다. 시행 헤더와 정오답 문구는 블록 전에 미리 준비합니다. 폰트 경로는 `NBACK_UI.font_path`에서 변경합니다. 외부 폰트 다운로드는 필요하지 않습니다. 화면의 물리적 해상도·macOS 배율에 따른 차이는 남을 수 있습니다.
- **안내·소리 확인·준비·휴식 화면은 흰색 배경**으로 통일했습니다. 상단 짙은 회색 띠 안에 큰 흰색 `DUAL-N-BACK` 제목을 표시합니다. Get ready는 수직 여정 목록, Sound check는 큰 알파벳과 재생 진행 표시, How to respond는 A/L 키 안내, Begin은 500ms/2,500ms 주기 도식으로 각각 다르게 구성했습니다. 실제 시행 화면은 기존 남색 배경과 푸른 사각형을 사용합니다.
- 하단 조작 안내는 **키보드 전용 버튼 모양**입니다. 마우스 클릭은 지원하지 않습니다. 소리 재생 중 SPACE를 누르면 현재·예약 재생을 멈추고 응답 방법 안내로 진행합니다. 이 조작은 다음 안내로 이동하며 참가자 반응 CSV에는 별도의 설정 행을 추가하지 않습니다.
- 각 블록 뒤에는 마지막 시행의 `Last: Visual ... / Auditory ...` 문구를 표시하지 않습니다. 블록 정답·오답 수, 정확도, `Current N → Next N`, 남은 휴식 시간을 표시하고 **10초 후 키 조작 없이 다음 블록으로 이동**합니다. 시각·청각 오류가 각각 3개 미만이면 N을 1 올리고, 어느 감각이든 5개를 초과하면 N을 1 내립니다(최소 1). 그 외에는 유지합니다. 오류가 양쪽에서 엇갈리면 감소를 우선하는 규칙은 재현 가정(`ASSUMPTIONS.decrease_rule="either"`)입니다. SPACE로 휴식을 단축하지 않으며 ESC로 중단할 수 있습니다. 3초 시작 준비는 첫 블록에만 적용하므로 블록 사이에 10+3초가 누적되지 않습니다. 마지막 블록에서는 SPACE로 종료합니다.
- 검사 중 상단에 `N=2 | Block 1/20 | Trial 1/20` 형태로 현재 난이도와 진행도를 계속 표시합니다. 피드백 글자 높이는 0.022에서 **0.044 height 단위(기존의 2배)**로 늘리고 `Visual`, `Auditory` 아래에 `Correct` / `Incorrect`만 표시합니다. 정답은 민트색, 오답은 부드러운 주황색입니다.
- `config.py`의 `NBACK_UI`에서 배경·카드·글자·피드백 색, `feedback_height`, `countdown_s`(첫 블록), `inter_block_rest_s`(블록 사이, 기본 10초)를 바꿀 수 있습니다. 흰색 안내 화면은 `flow_*` 설정으로 변경합니다. 사각형 색은 `DISPLAY.square_color`, 시작 N은 `ASSUMPTIONS.start_n`입니다. UI 설정은 참가자 반응 CSV에 포함하지 않습니다.
- 알파벳 WAV 8개는 `AUDIO_GENERATION.letter_names`의 `bee / eff / aitch / jay / em / cue / ar / double you`로 재생성했습니다. 대문자 문자열을 TTS에 전달하지 않아 `Capital` 안내어가 붙지 않도록 했습니다. 현재 8개 모두 시간축 압축 없이 500ms 파일 안에 들어갑니다. 숫자 음성은 기존과 같습니다.
- 색상·피드백 외형·단계 안내·카운트다운·10초 자동 휴식은 **사용자가 요청한 재현 변경/가정**이며 원논문 명시 조건이 아닙니다. 푸른색의 심리적 효과를 실증했다고 주장하지 않습니다. 준비·휴식 화면은 블록 밖에만 나타나며 500ms/2,500ms 자극 일정과 채점·적응 규칙을 유지합니다.
- 실제 PsychoPy로 캡처한 [시작 안내](data/smoke/ui_v5/welcome.png), [소리 확인](data/smoke/ui_v5/audio_playing.png), [응답 방법](data/smoke/ui_v5/instructions.png), [속도 안내](data/smoke/ui_v5/ready.png), [10초 휴식](data/smoke/ui_v5/break.png)을 확인할 수 있습니다. `tools/preview_nback_ui.py`로 다시 생성합니다.
- 화면 안내, 입력창, 반응 피드백, 실행 오류 메시지는 영어입니다. Reading Span 활성 CSV도 영어 초안으로 바꿨으며 `reviewed=no`를 유지합니다. 이전 한국어 초안은 `stimuli/archive/`에 보존했으며 프로그램은 읽지 않습니다. 한국어 코드 주석과 이 설명서는 코드 학습을 위해 유지했습니다.
- **A는 시각 위치가 N개 전과 일치할 때, L은 청각 자음이 N개 전과 일치할 때** 누릅니다. 둘 다 일치하면 두 키, 둘 다 불일치하면 무반응입니다.
- 응답 가능한 구간은 각 시행의 **0 ≤ RT < 3초**입니다. 500ms 후 사각형이 사라져도 계속 응답할 수 있습니다. 예를 들어 2.7초의 A 반응은 그 시행에 속하며 다음 시행은 원래 일정대로 진행됩니다.
- 첫 유효 A/L 키 반응 뒤 다음 화면 갱신에서 해당 감각의 `Correct` 또는 `Incorrect`을 표시합니다. 양쪽 감각은 별도로 표시됩니다. 반복 입력은 점수와 최초 RT를 바꾸지 않으며 실제 키와 RT 목록에는 모두 남깁니다.
- 무응답의 정오는 3초가 끝난 뒤에만 확정합니다. Target 무응답은 `Incorrect`, Non-target 무응답은 `Correct`입니다. 무응답 결과도 개별 시행과 블록 점수에 남깁니다.
- `NBACK_FEEDBACK.enabled`에서 현재 반응 피드백 사용 여부를 바꿀 수 있습니다. **시행 중 즉시 피드백은 사용자가 추가한 조건이며, 원논문 본문에 명시된 조건이라고 주장하지 않습니다.**
- 첫 N개는 기억을 채우는 준비 시행이며, 그 뒤 **채점 시행 20개**가 진행됩니다. 화면에 `Warm-up` / `Trial 1/20` 등을 구분합니다. 준비 시행의 반응 피드백은 표시하되 적응 난이도 채점에서는 제외합니다.
- 자음은 공유 PTB 출력 장치에서 미리 로드하고 사각형과 같은 onset에 예약합니다. 재생 예약과 반응은 기존 공통 프레임 일정으로 처리하지만 음성별 시각은 저장하지 않습니다.
- 시작 전 **Audio check**에서 자음 8개를 듣습니다. 재생 중 SPACE로 즉시 건너뛸 수 있습니다. 모두 들은 뒤 확인 화면에서는 SPACE로 확인, R로 다시 듣기, D로 출력 장치 선택을 합니다. 들리지 않으면 D로 헤드폰/스피커를 선택하고 시스템 음량·음소거를 확인하세요. 장치·청취 확인용 별도 파일은 생성하지 않습니다.
- `AUDIO_PLAYBACK`의 `device_name`, `volume`, `schedule_lead_s`를 설정할 수 있습니다. `check_before_session=False`는 자동 기술 검사에만 사용하고, 실제 수집에서는 청취 확인 사용 여부와 참가자의 건너뛰기 여부를 구분해 확인하세요.
- 실시간 채점은 hit / miss / false alarm / correct rejection을 구분합니다. 파일에는 감각별 개별 outcome과 블록 정답·오답 수·전체 정확도를 남깁니다. 피드백 표시 시각·문구는 저장하지 않습니다.

| 실제 상태 | A 또는 L의 해당 감각 반응 | 결과 |
|---|---|---|
| Target (일치) | 3초 내 해당 키 | Hit — Correct |
| Target (일치) | 무응답 | Miss — Incorrect |
| Non-target (불일치) | 무응답 | Correct Rejection — Correct |
| Non-target (불일치) | 해당 키 | False Alarm — Incorrect |

실제 화면은 디스플레이 프레임에 맞춰 갱신되므로 3초는 명목 일정입니다. 키 입력·피드백 때문에 멈추거나 조기 종료하지 않지만, 운영체제/디스플레이 지연이 있을 수 있습니다. 요약 전용 버전에는 개별 flip 기록이 없습니다.

## 빠른 실행: macOS PsychoPy Coder

1. [공식 설치 페이지](https://psychopy.org/download.html)에서 macOS용 **PsychoPy Standalone**을 설치합니다. 이 컴퓨터의 Standalone **2026.2.4**로 실제 실행을 검사했습니다. 시스템 Python과 Standalone에 내장된 Python은 서로 다를 수 있습니다.
2. PsychoPy를 열고 Coder에서 이 폴더의 `main.py`를 엽니다. Run을 누릅니다.
3. `email`에는 본인의 한양대학교 이메일(예: `student01@hanyang.ac.kr`), `task`에는 과제를 선택합니다. Dual N-back은 `phase=training`, Span은 `pretest` 또는 `posttest`를 선택합니다.
4. Digit Span은 `mode=forward` 또는 `backward`를 골라 **각각 별도로 실행**합니다. 두 방향의 중단 규칙과 점수는 독립적입니다.
5. 실제 실험은 헤드폰을 연결하여 17개 음성의 발음·음량을 확인한 뒤 시작합니다. 작업용 창 모드가 기본입니다. 시작 설정 창에서 `fullscreen`을 체크하면 전체 화면을 사용합니다. 창 크기·기본 전체 화면 설정은 `config.py`의 `DISPLAY`에서 변경합니다.
6. 데이터는 실행 위치와 관계없이 이 프로젝트의 `data/`에 저장됩니다. ESC 또는 회상 입력창의 취소는 중단으로 기록됩니다.

PsychoPy가 설치된 Python 환경에서는 다음 명령도 가능합니다.

```bash
python main.py --task dual_nback --email student01@hanyang.ac.kr --phase training --fullscreen
python tasks/digit_span.py --email student01@hanyang.ac.kr --phase pretest --mode forward
python tasks/digit_span.py --email student01@hanyang.ac.kr --phase posttest --mode backward
python tasks/reading_span.py --email student01@hanyang.ac.kr --phase pretest
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
| `stimuli/text.py` | 네이티브 해상도 폰트를 어떻게 렌더링·캐시하는가? |
| `stimuli/nback_ui.py` | 단계별 안내·소리 확인·준비·휴식 화면을 어떻게 그리는가? |
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
5. 각 감각에서 첫 유효 키 반응으로 반응 유무와 RT를 정하고, 반복 키는 점수와 최초 RT를 바꾸지 않습니다. RT는 해당 시각 자극 시작 기준 초입니다. 각 감각 오류는 miss + false alarm입니다.
6. 양쪽 오류가 모두 0~2이면 N+1, 어느 한쪽이라도 6개 이상이면 N-1, 나머지는 유지합니다. 최소 N=1이며 상한은 두지 않았습니다. 시작 N은 매 실행 2입니다.

시행별 onset/offset·키·RT를 저장합니다. onset/offset은 블록 시작 기준 소프트웨어 화면 시각이며 음성의 물리적 도착 시각은 아닙니다. 프레임별 진단 목록과 장치 설정은 저장하지 않습니다.

### Digit Span

- 영어 숫자 WAV를 1초 간격으로 예약 재생합니다. 숫자는 1~9이며 바로 인접한 반복을 금지합니다.
- Forward 3~9, Backward 2~8, 길이마다 2회입니다. 같은 길이에서 2회 모두 실패하면 해당 방향의 본검사를 종료합니다.
- 방향별 연습은 최단 길이 2회이며 정답 피드백을 제공합니다. 본검사에서는 정답을 보여주지 않습니다.
- 마지막 숫자의 1초 슬롯이 끝난 뒤 숫자 키로 입력하고 Enter로 제출합니다. Backspace로 수정할 수 있고, 입력 길이를 강제하지 않으며 누락·과다 응답도 점수 계산에 반영합니다. 개별 자극·정답 순서·입력 결과와 키 이벤트를 저장합니다.
- `exact_serial_accuracy`: 완전히 맞은 시행 수 / 시행 수. `total_correct`: 완전히 맞은 시행 수. `maximum_span`: 한 번 이상 완전히 회상한 가장 긴 길이, 없으면 0입니다.
- 기본 seed는 정규화한 한양대학교 이메일에서 안정적으로 계산됩니다. 같은 이메일와 같은 설정을 유지하면 Pre/Post 및 두 방향·연습 사이에 동일 숫자 시퀀스를 재사용하지 않습니다. `--seed`를 직접 지정한다면 Pre/Post에서 같은 값을 사용해야 이 보장이 유지됩니다. 설정 변경 후 수집한 자료는 같은 검사 버전으로 간주하지 마세요.

### Reading Span

- Pretest=A, Posttest=B입니다. 각 form은 2·3·4·5문장 세트를 크기별 3개씩, 총 12세트·42문장으로 구성합니다. 연습은 별도 P form의 2문장×3세트입니다.
- 본검사에서는 **세트 순서만 무작위화**하고 세트 안의 문장 순서는 CSV의 `item_order`를 따릅니다. form 전체 True/False가 21/21이며, 연습은 3/3입니다.
- Y=True, N=False로 문장이 말이 되는지 판단하며 마지막 **단어**을 기억합니다. 키는 config에서 변경할 수 있습니다. 영어 초안의 `recall_word`는 문장 끝 문장부호를 제외한 마지막 단어입니다.
- 연습 문장의 판단은 시간 제한이 없습니다. 최신 연습 수행에서 **정답 판단한 문장의 RT만** 사용하여 `평균 + 2.5 × 표본 SD(ddof=1)`를 계산합니다. 유효 RT가 2개 미만이면 연습을 다시 합니다. SD=0도 그대로 적용합니다.
- 본검사에서 무응답 timeout은 처리 오답으로 채점합니다. 모든 세트를 진행하며 조기 중단하지 않습니다.
- 세트가 끝나면 입력창에 단어를 공백으로 구분하여 순서대로 입력합니다. 기억나지 않는 위치에는 `_`를 입력하여 뒤의 단어 위치를 보존합니다. 키보드로 여러 단어를 입력하기 위해 PsychoPy GUI 입력창(Qt/wx)을 사용합니다.
- `processing_accuracy`: 정답 의미 판단 수 / 제시 문장 수. **85% 미만**이면 `processing_below_threshold=True`입니다. 자동으로 참가자를 제외하지 않습니다.
- `position_correct_partial_credit`: 각 세트의 위치 정답 비율을 구한 뒤 세트 간 평균을 냅니다. 길이에 따른 가중 차이를 확인하도록 `item_accuracy`(전체 위치 정답 수 / 전체 단어 수)도 함께 저장합니다.
- `complete_set_accuracy`: 모든 단어와 길이가 정확한 세트 수 / 세트 수입니다. 단어의 단순 포함 여부가 아니라 **동일 위치**인지 비교합니다. 공백 분리 외의 자동 철자·조사·동의어 보정은 하지 않습니다.
- 회상 RT는 회상 안내 시작부터 제출까지의 시간으로 저장합니다. 개별 단어의 검색 시간으로 해석하지 않습니다.

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

## 데이터 파일: 참가자 반응 CSV 하나

매 실행에서 `data/<과제>_<시각>_<고유번호>_responses.csv` **한 파일만** 생성합니다. Excel에서 열 수 있는 UTF-8 BOM CSV입니다. JSONL, session CSV, block summary CSV, 기술 진단 파일을 추가로 생성하지 않습니다. 기존 기록 파일은 그대로 둡니다.

Dual N-back은 **한 행 = 한 시행**이며 두 감각의 반응을 같은 행에 보존합니다.

| 주요 열 | 의미 |
|---|---|
| `participant`, `session_id`, `phase` | 정규화한 한양대학교 이메일·실행·검사 단계 구분 |
| `block`, `n`, `trial_number` | 블록·난이도·블록 내 시행 번호(1부터, 준비 시행 포함) |
| `visual_position`, `visual_x`, `visual_y` | 0~7 위치 ID, 중심 기준 height 좌표 |
| `auditory_letter` | 실제 청각 알파벳 |
| `visual_target`, `auditory_target` | N개 전 자극과의 일치 여부 |
| `visual_key`, `auditory_key`, `response_window_s` | 사후 재채점을 위한 반응 키·유효 반응 창 |
| `visual_rt_s`, `auditory_rt_s` | 감각별 첫 유효 반응 RT(초), 무응답이면 빈칸 |
| `visual_responded`, `auditory_responded` | 반응 유무 |
| `visual_correct`, `auditory_correct` | 감각별 정오답 |
| `visual_outcome`, `auditory_outcome` | hit / miss / false_alarm / correct_rejection |
| `response_keys`, `response_rts_s`, `response_first_flags` | 수집된 모든 유효 A/L 입력과 RT·최초 입력 여부. 반복·동시 반응 포함. 세미콜론으로 구분하며 같은 순서끼리 대응 |
| `warmup`, `scored`, `complete` | 준비 시행·분석 포함·응답 창 완료 여부 |
| `onset_s`, `offset_s` | 블록 시작 기준 시각 자극 시작·종료 시각 |
| `block_*_correct`, `block_*_incorrect`, `block_*_accuracy_pct` | 해당 블록 감각별 정답·오답 수·정확도(0~100) |
| `block_scored_trials`, `next_n` | 블록 정확도 분모와 다음 난이도 |
| `session_status` | completed / aborted / error / closed_without_status 등 세션 종료 상태 |

예: `response_keys=a;l;a`, `response_rts_s=0.4;0.4;0.7`, `response_first_flags=1;1;0`이면 두 키를 0.4초에 함께 누르고 A를 0.7초에 다시 누른 것입니다. 최초 감각별 RT는 두 감각 모두 0.4초이며 반복 입력으로 바뀌지 않습니다. 반응 창 밖의 입력이나 관련 없는 키는 과제의 유효 반응이 아닙니다.

분석에서는 기본적으로 `scored=True`, `complete=True`를 사용합니다. 무응답을 RT=0으로 바꾸지 마세요. 중단된 시행은 자극·현재까지 수집한 키·RT를 남기되 `complete=False`, `scored=False`로 표시하고 아직 확정할 수 없는 정오답·outcome은 빈칸으로 둡니다. 블록을 끝내지 못하면 그 블록의 정확도 열은 비어 있습니다. 블록 통계는 해당 블록 시행 행들에 반복되므로 블록별로 한 번만 읽으며, 반복된 값을 합산하지 않습니다.

Digit Span도 같은 파일명 규칙의 단일 CSV에 자극 숫자·정답 순서·회상 결과·RT·정오답·숫자 키 이벤트를 기록합니다. Reading Span은 `event_type=sentence_judgment/reading_recall`로 문장 판단과 세트 회상을 구분하고 문장·정답·최종 응답·RT·위치별 점수를 보존합니다. 배열·숫자 키 이벤트는 CSV 셀 안의 JSON 문자열이며 별도 JSON 파일은 만들지 않습니다. `stage=practice/test`를 구분해 분석하세요. 제시 시작 후 중단된 Span 문항은 `*_incomplete` 행으로 구분하며 완성된 응답처럼 채점하지 않습니다.

N-back 원반응은 프레임 타이밍에 디스크 쓰기가 영향을 주지 않도록 블록 종료 또는 ESC 중단 시 저장합니다. 저장된 행은 즉시 flush합니다. 종료 시 같은 CSV의 상태 열을 갱신합니다. 강제 프로세스 종료 시 진행 중 블록은 유실될 수 있고, 이미 저장된 행의 상태는 `running`으로 남을 수 있습니다. 실행 전 중단해 실제 시행이 없으면 헤더만 남습니다.

`utils/data_logger.py`가 저장 정책을 관리하고 `utils/participant.py`가 이메일 형식을 검사합니다. `tools/report_timing.py`는 이전 버전 JSONL을 읽는 도구이므로 새 CSV에는 사용하지 않습니다. 기존 JSONL·trial CSV는 이전 기록으로 유지되며, 새 형식으로 자동 변환하거나 삭제하지 않습니다.

## 오디오와 자극

- `stimuli/audio/{B,F,H,J,M,Q,R,W}.wav`: 48 kHz, mono PCM16, 500ms.
- `stimuli/audio/digits/{1..9}.wav`: 같은 형식, 950ms 파일. 자극 시작 간격은 1초입니다.
- `stimuli/audio/manifest.json`: 합성 목소리, 속도, 원래 길이와 시간축 압축 여부.
- `tools/generate_audio.py`: `config.py`의 `AUDIO_GENERATION` 설정과 macOS `say`와 `afconvert`로 파일을 다시 만드는 도구.

합성음은 Samantha 영어 목소리로 만들었습니다. 선행/후행 무음을 정리하며, 현재 알파벳 8개는 압축 없이 500ms 안에 들어갑니다. 합성 속도나 발음 설정을 바꿔 길이가 넘치면 생성 도구가 전체 파형을 시간축 재표본화합니다. 그 경우 음높이·명료도에 영향을 줄 수 있으며 manifest의 compressed 필드에 남습니다. 원논문의 음성 녹음과 동일하지 않으며, 청취와 판별 가능성 검토가 필요합니다. 실제 녹음으로 교체할 때 파일명과 PCM 형식을 유지하고 `manifest.json`과 실험 버전을 갱신하세요. 사각형은 코드로 생성하므로 별도 그림 파일이 필요하지 않습니다.

## Reproduction assumptions 및 비교 체크리스트

| 항목 | 원문 또는 사용자 명세 | 구현·구분 |
|---|---|---|
| 위치·자음 수 | 원문: 각각 8개 | 구현. 위치는 중심을 제외한 3×3 배열 |
| 제시·ISI | 원문: 500ms / 2,500ms | 프레임 양자화하여 구현, 시행별 onset/offset 저장, 프레임별 진단 목록 미저장 |
| 반응 키 | 원문: 시각 A / 청각 L | 구현, 비일치 무반응·동시 target 두 키 |
| 시행·블록 수 | 원문: 20+N / 세션 20블록 | 구현 |
| target | 원문: 감각별 6, 중복 2 | 생성 후 실제 일치까지 단위 테스트 |
| N 증가 | 원문: 감각별 오류 3 미만 | 양쪽 모두 2개 이하일 때 증가 |
| N 감소 | 원문: 오류 5 초과, 감각 결합 방식 불명확 | 사용자 승인 가정: 어느 한쪽 6개 이상 |
| 시작·최소 N | 본문 미명시 | 사용자 승인 가정: 2 / 1; 세션 간 자동 승계 없음 |
| 응답·준비 시행 | 상세 기준 미명시 | 사용자 승인 가정: 전체 3초, 첫 N개 적응 채점 제외 |
| 음성·자음 목록 | 정확한 녹음·목록 본문 미명시 | 승인 가정: B F H J M Q R W, 영어 합성음 |
| 화면 외형 | 픽셀 크기·색·거리 미명시 | 사용자 변경: 흰색 단계 안내, 시행 남색 배경·푸른 사각형·아래쪽 감각별 피드백·N 표시 |
| 화면 모드·글자 | 해상도·폰트 상세 미명시 | 사용자 변경: 전체 화면 선택, Helvetica 네이티브 픽셀 렌더링 |
| 블록 요약 | 표시 지표 상세 미명시 | 사용자 변경: 감각별 정답·오답 수 및 전체 정확도 표시·저장 |
| 시작 안내·준비 | 단계형 UI·카운트다운 미명시 | 사용자 변경: 단계 안내·속도 예고·첫 블록 전 3초 준비, 블록 사이 10초 자동 휴식 |
| 오류 정의·반복 키 | 상세 처리 미명시 | miss+false alarm; 감각별 1회 채점, 반복 원자료 보존 |
| 피드백·휴식 | 세부 운영 미명시 | 블록 뒤 오류·다음 N 표시, 사용자 변경: 10초 후 자동 진행 |
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

`tools/smoke_psychopy.py`는 기본 한 블록의 실제 화면·음성을 자동 실행하고 입력 대기를 넘깁니다. `--blocks 2 --audio-skip-check --scripted-responses`는 소리 확인의 SPACE 건너뛰기와 10초 자동 휴식을 실제 화면에서 검사합니다. 기본은 ISI를 짧게 한 기술 검사이며, `--full-timing`을 붙이면 500ms/2,500ms 조건입니다. `tools/smoke_digit.py`는 두 방향의 숫자를 실제 재생하되 회상 답을 자동 오답으로 대체하여 중단 규칙까지 실행합니다. 이 결과는 `data/smoke/`에 저장하며 연구 자료로 사용하지 않습니다.

검증 결과와 한계는 `VALIDATION.md`에 기록했습니다. 자동 검사에서 정상 실행되었다는 사실은 키보드의 실제 사람 반응, 영어 단어 입력, 음성의 청각적 명료도, 20블록 전체의 안정성, 물리적 시청각 동기의 검증을 뜻하지 않습니다.

## 근거 자료

- 사용자 첨부 Jaeggi et al. (2008), *Improving fluid intelligence with training on working memory*, pp. 6829–6833, 특히 p. 6832 Materials and Methods. DOI: [10.1073/pnas.0801268105](https://doi.org/10.1073/pnas.0801268105). [공개 본문](https://pmc.ncbi.nlm.nih.gov/articles/PMC2383929/)
- [PsychoPy 공식 설치 안내](https://psychopy.org/download.html)
- [PsychoPy 음성 예약 재생 안내](https://psychopy.org/api/sound/playback.html)

GitHub 연결로 관련 PsychoPy N-back 저장소를 검색했으나 타 저장소의 코드를 복사하거나 변형해 포함하지 않았습니다. 구현 근거는 첨부 원문, 사용자 지정 절차, PsychoPy API입니다. 기존 상위 폴더의 `nback.py`는 수정하지 않았습니다.
