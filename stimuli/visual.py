"""그리기만 담당. 시간·반응·flip은 tasks에서 관리."""

POSITIONS = [(-1, 1), (0, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (0, -1), (1, -1)]


class VisualStimuli:
    def __init__(self, win, settings):
        from psychopy import visual

        self.spacing = settings["spacing"]
        self.square = visual.Rect(
            win,
            width=settings["square_size"],
            height=settings["square_size"],
            fillColor=settings["square_color"],
            lineColor=settings["square_color"],
        )
        from stimuli.text import SharpText
        self.fixation = SharpText(win, text="+", height=0.035, color="#ACBDD3")
        self.fixation.prepare()

    def draw(self, position=None):
        self.fixation.draw()
        if position is not None:
            x, y = POSITIONS[position]
            self.square.pos = (x * self.spacing, y * self.spacing)
            self.square.draw()


class FeedbackDisplay:
    """하단 피드백만 그린다. wait/flip을 호출하지 않아 시행 일정을 바꾸지 않는다."""

    def __init__(self, win):
        from psychopy import visual
        from config import NBACK_UI, NBACK
        from stimuli.text import SharpText

        self.theme = NBACK_UI
        self.header = SharpText(
            win, height=0.038, pos=(0, 0.425), wrapWidth=1.2, autoLog=False)
        y = self.theme["feedback_y"]
        self.panels = [visual.Rect(
            win, width=0.55, height=self.theme["feedback_panel_height"], pos=(x, y),
            fillColor=self.theme["panel"], lineColor=self.theme["border"], autoLog=False
        ) for x in (-0.30, 0.30)]
        self.labels = [SharpText(
            win, text=f"{NBACK[key].upper()}  /  {label}", height=0.026,
            pos=(x, y + 0.040), color=self.theme["muted"], autoLog=False
        ) for x, key, label in ((-.30, "visual_key", "Visual"), (.30, "auditory_key", "Auditory"))]
        self.visual = SharpText(
            win, height=self.theme["feedback_height"], pos=(-0.30, y - 0.020),
            wrapWidth=0.53, autoLog=False)
        self.auditory = SharpText(
            win, height=self.theme["feedback_height"], pos=(0.30, y - 0.020),
            wrapWidth=0.53, autoLog=False)
        self.cache = {}

    def update(self, stimulus, text, color=None):
        color = color or self.theme["text"]
        value = (text, color)
        if self.cache.get(id(stimulus)) != value:
            stimulus.text = text
            stimulus.color = color
            self.cache[id(stimulus)] = value
        if text:
            stimulus.draw()

    def prepare(self, headers):
        for text in headers:
            self.header.prepare(text, self.theme["text"])
        for stimulus in (self.visual, self.auditory):
            stimulus.prepare("Correct", self.theme["correct"])
            stimulus.prepare("Incorrect", self.theme["incorrect"])
        for label in self.labels:
            label.prepare(label.text, self.theme["muted"])

    def draw(self, header, current):
        self.update(self.header, header)
        for modality, panel, label in zip(
            ("visual", "auditory"), self.panels, self.labels
        ):
            panel.draw()
            label.draw()
            result = current.get(modality, "")
            color = self.theme["correct"] if result == "Correct" else self.theme["incorrect"]
            self.update(getattr(self, modality), result, color)
