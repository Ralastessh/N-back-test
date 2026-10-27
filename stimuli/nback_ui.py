"""화이트 안내 화면. 시행 자극과 독립적으로 안내·휴식 시간만 관리한다."""

import math
from config import NBACK_UI, NBACK, ASSUMPTIONS
from stimuli.text import SharpText
from utils.scoring import nback_summary


class ParticipantScreens:
    def __init__(self, win):
        from psychopy import visual

        self.win = win
        self.visual = visual
        self.theme = NBACK_UI
        self.texts = {}
        self.panels = {}

    def text(self, name, text, pos, height=.03, color=None, width=1.1):
        color = color or self.theme["flow_text"]
        if name not in self.texts:
            self.texts[name] = SharpText(
                self.win, autoLog=False, text="", units="height")
        item = self.texts[name]
        item.pos, item.height, item.wrapWidth = pos, height, width
        item.color = color
        if item.text != text:
            item.text = text
        item.draw()

    def panel(self, name, pos, size, color=None, border=None):
        if name not in self.panels:
            self.panels[name] = self.visual.Rect(self.win, autoLog=False, units="height")
        item = self.panels[name]
        item.pos = pos
        item.width, item.height = size
        item.fillColor = color or self.theme["flow_panel"]
        item.lineColor = border or item.fillColor
        item.draw()

    def base(self, step=None):
        self.win.color = self.theme["flow_background"]
        self.panel("flow_background", (0, 0), (3, 1), self.theme["flow_background"])
        # 흰 화면에서 흰 제목을 읽을 수 있도록 상단에 짙은 중립색 띠를 둔다.
        self.panel("masthead", (0, .44), (3, .12), self.theme["flow_header"])
        self.text("brand", "DUAL-N-BACK", (0, .44), .042, "white")
        if step is not None:
            for i, label in enumerate(("01  Get ready", "02  Sound check", "03  How to respond", "04  Begin")):
                x = -.45 + i * .30
                self.text(f"step{i}", label, (x, .325), .022,
                          self.theme["flow_text"] if i == step else self.theme["flow_muted"], .29)
                self.panel(f"step_line{i}", (x, .285), (.265, .005),
                           self.theme["flow_accent"] if i == step else self.theme["flow_border"])

    def buttons(self, primary="Continue", extras=()):
        buttons = ([] if primary is None else [("SPACE", primary)]) + list(extras) + [("ESC", "Exit")]
        count = len(buttons)
        width = min(.36, 1.18 / count - .025)
        for i, (key, label) in enumerate(buttons):
            x = (i - (count - 1) / 2) * (width + .025)
            dark = key == "SPACE"
            self.panel(f"button{i}", (x, -.425), (width, .065),
                       self.theme["flow_header"] if dark else self.theme["flow_panel"],
                       self.theme["flow_header"] if dark else self.theme["flow_border"])
            self.text(f"button_text{i}", f"{key}   {label}", (x, -.425), .020,
                      "white" if dark else self.theme["flow_text"], width - .01)

    def wait(self, kb, renderer, *args, keys=("space", "escape")):
        renderer(*args)
        self.win.callOnFlip(kb.clearEvents)
        self.win.flip()
        key = kb.waitKeys(keyList=list(keys), waitRelease=False)[0].name
        if key == "escape":
            raise KeyboardInterrupt
        return key

    def draw_welcome(self):
        self.base(0)
        self.text("welcome_title", "A moment to get ready", (0, .185), .050)
        self.text("welcome_note", "Remember locations and letters, one step at a time.", (0, .105), .026,
                  self.theme["flow_muted"])
        # 시작 화면은 수직 여정 목록: 세 개의 반복 카드 대신 한 흐름으로 읽는다.
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

    def draw_audio(self, letter=None, index=0):
        self.base(1)
        self.text("audio_title", "Listen for each letter" if letter else "Sound clear?", (0, .19), .045)
        self.text("audio_note", "Adjust your volume, or press SPACE to skip." if letter else
                  "Did you hear the spoken letters clearly?", (0, .115), .026, self.theme["flow_muted"])
        self.text("audio_letter", letter or "Ready", (0, -.035), .13 if letter else .075,
                  self.theme["flow_accent"])
        if letter:
            for i in range(len(ASSUMPTIONS["consonants"])):
                self.panel(f"audio_tick{i}", ((i - 3.5) * .07, -.18), (.045, .009),
                           self.theme["flow_accent"] if i <= index else self.theme["flow_border"])
            self.text("audio_progress", f"{index + 1} / {len(ASSUMPTIONS['consonants'])}", (0, -.24), .024,
                      self.theme["flow_muted"])
            self.buttons("Skip")
        else:
            self.text("audio_choices", "Replay if needed, or choose a different output device.", (0, -.20), .025,
                      self.theme["flow_muted"])
            self.buttons("Continue", (("R", "Replay"), ("D", "Output")))

    def draw_instructions(self):
        self.base(2)
        self.text("keys_title", "Two streams. Two keys.", (0, .19), .048)
        self.text("keys_note", "Compare with the location and letter N turns earlier.", (0, .11), .026,
                  self.theme["flow_muted"])
        for x, modality, key, detail in ((-.30, "Visual", NBACK["visual_key"], "Same location"),
                                         (.30, "Auditory", NBACK["auditory_key"], "Same letter")):
            self.panel(modality + "_surface", (x, -.07), (.55, .25))
            self.panel(modality + "_key", (x, -.015), (.105, .09), "white", self.theme["flow_border"])
            self.text(modality + "_keytext", key.upper(), (x, -.015), .048)
            self.text(modality + "_name", modality, (x, -.10), .032)
            self.text(modality + "_detail", detail, (x, -.155), .025, self.theme["flow_muted"], .5)
        self.text("keys_rule", "Both match: press both keys.     Neither matches: press nothing.", (0, -.265), .025)
        self.buttons()

    def draw_ready(self):
        self.base(3)
        interval = NBACK["stimulus_s"] + NBACK["isi_s"]
        self.text("ready_title", "Find a steady rhythm", (0, .19), .048)
        self.text("ready_note", "The task moves quickly. Missed a turn? Keep going.", (0, .11), .026,
                  self.theme["flow_muted"])
        self.text("rhythm_title", f"One turn every {interval:g} seconds", (0, .015), .033)
        self.panel("rhythm_track", (0, -.065), (1.08, .045), self.theme["flow_panel"])
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

    def draw_countdown(self, n, block, remaining):
        self.base(3)
        self.text("count_title", f"Block {block}/{NBACK['blocks']}  /  N={n}", (0, .17), .035)
        self.text("count_number", str(remaining), (0, -.015), .14, self.theme["flow_accent"])
        self.text("count_note", "Get ready for the first location and letter.", (0, -.19), .027)
        self.buttons(None)

    def countdown(self, kb, n, block, frame_s):
        for frame in range(round(NBACK_UI["countdown_s"] / frame_s)):
            if kb.getKeys(keyList=["escape"], waitRelease=False):
                raise KeyboardInterrupt
            self.draw_countdown(n, block, max(1, math.ceil(NBACK_UI["countdown_s"] - frame * frame_s)))
            self.win.flip()

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
        stats = nback_summary(errors, NBACK["scored_trials"] if total is None else total)
        for modality, y in (("visual", .06), ("auditory", -.075)):
            result = stats[modality]
            self.text("summary_" + modality, f"{modality.title()}   {result['accuracy']:.0%}",
                      (.33, y), .032, width=.52)
            self.text("summary_" + modality + "_counts",
                      f"Correct {result['correct']} / {result['total']} | Incorrect {result['incorrect']}",
                      (.33, y - .052), .022, self.theme["flow_muted"], .54)
        self.text("summary_n", f"Final N={n}" if finished else f"Current N={n}  →  Next N={next_n}", (0, -.215), .03)
        self.text("summary_help", "Thank you for taking part." if finished else "Relax your hands. The next block starts automatically.",
                  (0, -.28), .025, self.theme["flow_muted"])
        self.buttons("Finish" if finished else None)

    def inter_block_rest(self, kb, block, n, next_n, errors, total=None):
        """첫 휴식 flip부터 실제 경과시간 측정. SPACE로 단축하지 않는다."""
        from psychopy import core

        duration = NBACK_UI["inter_block_rest_s"]
        clock = core.Clock()
        self.draw_summary(block, n, next_n, errors, math.ceil(duration), total=total)
        self.win.callOnFlip(kb.clearEvents)
        self.win.callOnFlip(clock.reset)
        self.win.flip()
        while clock.getTime() < duration:
            if kb.getKeys(keyList=["escape"], waitRelease=False):
                raise KeyboardInterrupt
            remaining = max(1, math.ceil(duration - clock.getTime()))
            self.draw_summary(block, n, next_n, errors, remaining, total=total)
            self.win.flip()
        return clock.getTime()

    def completion(self, kb, block, n, errors, total=None):
        self.wait(kb, lambda: self.draw_summary(block, n, n, errors, total=total))
