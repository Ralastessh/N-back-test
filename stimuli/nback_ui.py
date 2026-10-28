import math
from psychopy import core, visual
from config import NBACK_UI, NBACK, ASSUMPTIONS
from stimuli.text import SharpText
from utils.scoring import nback_summary

# Dual N-back의 안내 화면, 오디오 확인, 휴식 및 종료 화면을 관리
class ParticipantScreens:
    def __init__(self, win):
        self.win = win
        self.visual = visual
        self.theme = NBACK_UI
        # 같은 이름의 자극 객체를 재사용하여 반복적인 객체 생성을 방지
        self.texts = {}
        self.panels = {}

    # 화면에 표시할 글자를 생성하거나 기존 객체를 재사용
    def text(self, name, text, pos, height=.03, color=None, width=1.1):
        color = color or self.theme["flow_text"]
        if name not in self.texts:
            self.texts[name] = SharpText(
                self.win, text="")
        item = self.texts[name]
        item.pos, item.height, item.wrapWidth = pos, height, width
        item.color = color
        item.text = text
        item.draw()

    # 배경이나 버튼 등 사각형 형태의 UI를 표시
    def panel(self, name, pos, size, color=None, border=None):
        if name not in self.panels:
            self.panels[name] = self.visual.Rect(self.win, autoLog=False, units="height")
        item = self.panels[name]
        item.pos = pos
        item.width, item.height = size
        item.fillColor = color or self.theme["flow_panel"]
        item.lineColor = border or item.fillColor
        item.draw()

    # 모든 안내 화면에 공통으로 사용하는 배경과 상단 진행 단계 표시
    def base(self, step=None):
        self.win.color = self.theme["flow_background"]
        self.panel("flow_background", (0, 0), (3, 1), self.theme["flow_background"])
        self.panel("masthead", (0, .44), (3, .12), self.theme["flow_header"])
        self.text("brand", "DUAL-N-BACK", (0, .44), .042, "white")

        if step is not None:
            for i, label in enumerate(("01  Get ready", "02  Sound check", "03  How to respond", "04  Begin")):
                x = -.45 + i * .30
                self.text(f"step{i}", label, (x, .325), .022,
                          self.theme["flow_text"] if i == step else self.theme["flow_muted"], .29)
                self.panel(f"step_line{i}", (x, .285), (.265, .005),
                           self.theme["flow_accent"] if i == step else self.theme["flow_border"])

    # 화면 하단에 키보드 선택지를 버튼 형태로 표시
    def buttons(self, primary="Continue", extras=()):
        buttons = ([] if primary is None else [("SPACE", primary)]) + list(extras) + [("ESC", "Exit")]
        count = len(buttons)
        width = min(.36, 1.18 / count - .025)

        # 선택지 개수에 따라 버튼의 너비와 위치를 자동으로 조절
        for i, (key, label) in enumerate(buttons):
            x = (i - (count - 1) / 2) * (width + .025)
            dark = key == "SPACE"
            self.panel(f"button{i}", (x, -.425), (width, .065),
                       self.theme["flow_header"] if dark else self.theme["flow_panel"],
                       self.theme["flow_header"] if dark else self.theme["flow_border"])
            self.text(f"button_text{i}", f"{key}   {label}", (x, -.425), .020,
                      "white" if dark else self.theme["flow_text"], width - .01)

    # 안내 화면을 표시한 뒤 참가자의 키 입력을 기다리는 함수
    def wait(self, kb, renderer, *args, keys=("space", "escape")):
        # 창 크기가 변경되어도 현재 안내 화면을 다시 그릴 수 있도록 설정
        self.win._resize_draw = lambda: renderer(*args)
        try:
            renderer(*args)

            # 이전 화면에서 발생한 키 입력이 현재 선택에 영향을 주지 않도록 초기화
            self.win.callOnFlip(kb.clearEvents)
            self.win.flip()

            # 안내 화면에서는 참가자의 입력을 기다려도 실험 자극의 시간에 영향을 주지 않음
            key = kb.waitKeys(keyList=list(keys), waitRelease=False)[0].name
            if key == "escape":
                raise KeyboardInterrupt
            return key
        finally:
            self.win._resize_draw = None

    # 실험 시작 전 전체 진행 과정을 간단하게 안내
    def draw_welcome(self):
        self.base(0)
        self.text("welcome_title", "A moment to get ready", (0, .185), .050)
        self.text("welcome_note", "Remember locations and letters, one step at a time.", (0, .105), .026,
                  self.theme["flow_muted"])

        # 오디오 확인, 반응 방법 학습, 실험 시작 순서로 진행 절차를 표시
        for i, (heading, detail) in enumerate((
            ("Listen", "Check your audio at a comfortable volume."),
            ("Learn", "Use two keys to respond to matching stimuli."),
            ("Begin", "Work in short blocks with automatic breaks."),
        )):
            y = -.015 - i * .102
            self.panel(f"journey_mark{i}", (-.50, y), (.06, .06), self.theme["flow_panel"])
            self.text(f"journey_number{i}", str(i + 1), (-.50, y), .026)
            self.text(f"journey_title{i}", heading, (-.32, y), .031, width=.25)
            self.text(f"journey_detail{i}", detail, (.18, y), .024, self.theme["flow_muted"], .70)
        self.buttons("Sound check")

    def welcome(self, kb):
        self.wait(kb, self.draw_welcome)

    # 실제 실험 전에 자음 음성이 정상적으로 들리는지 확인하는 화면
    def draw_audio(self, letter=None, index=0):
        self.base(1)
        self.text("audio_title", "Listen for each letter" if letter else "Sound clear?", (0, .19), .045)
        self.text("audio_note", "Adjust your volume, or press SPACE to skip." if letter else
                  "Did you hear the spoken letters clearly?", (0, .115), .026, self.theme["flow_muted"])
        self.text("audio_letter", letter or "Ready", (0, -.035), .13 if letter else .075,
                  self.theme["flow_accent"])

        if letter:
            # 현재 몇 번째 자음을 확인하고 있는지 진행 상황 표시
            for i in range(len(ASSUMPTIONS["consonants"])):
                self.panel(f"audio_tick{i}", ((i - 3.5) * .07, -.18), (.045, .009),
                           self.theme["flow_accent"] if i <= index else self.theme["flow_border"])
            self.text("audio_progress", f"{index + 1} / {len(ASSUMPTIONS['consonants'])}", (0, -.24), .024,
                      self.theme["flow_muted"])
            self.buttons("Skip")
        else:
            # 음성이 불명확한 경우 다시 듣거나 출력 장치를 변경할 수 있도록 함
            self.text("audio_choices", "Replay if needed, or choose a different output device.", (0, -.20), .025,
                      self.theme["flow_muted"])
            self.buttons("Continue", (("R", "Replay"), ("D", "Output")))

    # 시각과 청각의 Target 판단 방법 및 반응 키 안내
    def draw_instructions(self):
        self.base(2)
        self.text("keys_title", "Two streams. Two keys.", (0, .19), .048)
        self.text("keys_note", "Compare with the location and letter N turns earlier.", (0, .11), .026,
                  self.theme["flow_muted"])

        # 시각 자극은 A, 청각 자극은 L처럼 감각별로 독립적인 반응 키를 제시
        for x, modality, key, detail in ((-.30, "Visual", NBACK["visual_key"], "Same location"),
                                         (.30, "Auditory", NBACK["auditory_key"], "Same letter")):
            self.panel(modality + "_surface", (x, -.07), (.55, .25))
            self.panel(modality + "_key", (x, -.015), (.105, .09), "white", self.theme["flow_border"])
            self.text(modality + "_keytext", key.upper(), (x, -.015), .048)
            self.text(modality + "_name", modality, (x, -.10), .032)
            self.text(modality + "_detail", detail, (x, -.155), .025, self.theme["flow_muted"], .5)

        # 두 감각이 모두 일치하는 경우와 모두 불일치하는 경우도 사전에 안내
        self.text("keys_rule", "Both match: press both keys.     Neither matches: press nothing.", (0, -.265), .025)
        self.buttons()

    # Trial의 고정된 진행 속도와 전체 블록 수를 안내
    def draw_ready(self):
        self.base(3)
        interval = NBACK["stimulus_s"] + NBACK["isi_s"]
        self.text("ready_title", "Find a steady rhythm", (0, .19), .048)
        self.text("ready_note", "The task moves quickly. Missed a turn? Keep going.", (0, .11), .026,
                  self.theme["flow_muted"])
        self.text("rhythm_title", f"One turn every {interval:g} seconds", (0, .015), .033)
        self.panel("rhythm_track", (0, -.065), (1.08, .045), self.theme["flow_panel"])

        # 전체 Trial 시간 중 실제 자극이 나타나는 시간의 비율을 시각적으로 표시
        segment = 1.08 * NBACK["stimulus_s"] / interval
        self.panel("rhythm_on", (-.54 + segment / 2, -.065), (segment, .045), self.theme["flow_accent"])

        self.text("rhythm_labels", f"{NBACK['stimulus_s']:g}s stimulus     +     {NBACK['isi_s']:g}s interval", (0, -.13), .024,
                  self.theme["flow_muted"])
        self.text("ready_stats", f"Start N={ASSUMPTIONS['start_n']}     /     {NBACK['blocks']} blocks     /     {NBACK_UI['inter_block_rest_s']:g}s breaks", (0, -.215), .028)
        self.text("ready_warmup", f"First N turns: memory warm-up. Respond within {ASSUMPTIONS['response_window_s']:g}s of each onset.", (0, -.285), .023,
                  self.theme["flow_muted"])
        self.buttons("Begin")

    def instructions(self, kb):
        self.wait(kb, self.draw_instructions)
        self.wait(kb, self.draw_ready)

    # 각 블록 시작 전에 현재 N-back 난이도와 남은 카운트다운 표시
    def draw_countdown(self, n, block, remaining):
        self.base(3)
        self.text("count_title", f"Block {block}/{NBACK['blocks']}  /  N={n}", (0, .17), .035)
        self.text("count_number", str(remaining), (0, -.015), .14, self.theme["flow_accent"])
        self.text("count_note", "Get ready for the first location and letter.", (0, -.19), .027)
        self.buttons(None)

    # 모니터 프레임 주기를 기준으로 카운트다운을 진행
    def countdown(self, kb, n, block, frame_s):
        for frame in range(round(NBACK_UI["countdown_s"] / frame_s)):
            if kb.getKeys(keyList=["escape"], waitRelease=False):
                raise KeyboardInterrupt

            # 프레임 경과에 따라 남은 초를 계산하고 화면 갱신
            self.draw_countdown(n, block, max(1, math.ceil(NBACK_UI["countdown_s"] - frame * frame_s)))
            self.win.flip()

    # 블록 종료 후 시각/청각 수행 결과와 다음 난이도를 표시
    def draw_summary(self, block, n, next_n, errors, remaining=None, total=None):
        self.base()
        finished = remaining is None
        self.text("summary_title", "Session complete" if finished else "Take a breath", (0, .26), .05)
        self.text("summary_note", f"Block {block}/{NBACK['blocks']} complete", (0, .175), .027,
                  self.theme["flow_muted"])

        if not finished:
            self.text("rest_number", str(remaining), (-.32, -.035), .14, self.theme["flow_accent"])
            self.text("rest_label", "seconds to next block", (-.32, -.15), .022, width=.5)
        else:
            self.text("rest_done", "Well done", (-.32, -.035), .055, self.theme["flow_accent"], .55)

        self.panel("summary_divider", (.025, -.05), (.003, .28), self.theme["flow_border"])

        # 감각별 오류 수를 바탕으로 각 블록의 정답률 계산
        stats = nback_summary(errors, NBACK["scored_trials"] if total is None else total)

        for modality, y in (("visual", .06), ("auditory", -.075)):
            result = stats[modality]
            self.text("summary_" + modality, f"{modality.title()}   {result['accuracy']:.0%}",
                      (.33, y), .032, width=.52)
            self.text("summary_" + modality + "_counts",
                      f"Correct {result['correct']} / {result['total']} | Incorrect {result['incorrect']}",
                      (.33, y - .052), .022, self.theme["flow_muted"], .54)

        self.text("summary_n", f"Final N={n}" if finished else f"Current N={n}  to  Next N={next_n}", (0, -.215), .03)
        self.text("summary_help", "Thank you for taking part." if finished else "Relax your hands. The next block starts automatically.",
                  (0, -.28), .025, self.theme["flow_muted"])
        self.buttons("Finish" if finished else None)

    # 블록 사이에는 일정한 휴식 시간을 주어 참가자의 부담을 조절
    def inter_block_rest(self, kb, block, n, next_n, errors, total=None):
        duration = NBACK_UI["inter_block_rest_s"]
        clock = core.Clock()

        self.draw_summary(block, n, next_n, errors, math.ceil(duration), total=total)

        # 휴식 화면이 실제로 표시되는 시점부터 경과시간 측정
        self.win.callOnFlip(kb.clearEvents)
        self.win.callOnFlip(clock.reset)
        self.win.flip()

        # 참가자 반응과 관계없이 설정된 휴식 시간을 고정
        while clock.getTime() < duration:
            if kb.getKeys(keyList=["escape"], waitRelease=False):
                raise KeyboardInterrupt

            remaining = max(1, math.ceil(duration - clock.getTime()))
            self.draw_summary(block, n, next_n, errors, remaining, total=total)
            self.win.flip()

        return clock.getTime()

    # 모든 블록이 끝나면 최종 수행 결과를 표시하고 종료 입력을 기다림
    def completion(self, kb, block, n, errors, total=None):
        self.wait(kb, lambda: self.draw_summary(block, n, n, errors, total=total))
