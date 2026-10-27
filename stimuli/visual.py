"""그리기만 담당. 시간·반응·flip은 tasks에서 관리."""

POSITIONS = [(-1, 1), (0, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (0, -1), (1, -1)]


class VisualStimuli:
    def __init__(self, win, settings):
        from psychopy import visual

        self.win = win
        self.frame_size = None
        self.spacing = settings["spacing"]
        self.square_size = settings["square_size"]
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
        frame_size = tuple(self.win.size)
        if frame_size != self.frame_size:
            # 원래 height 단위 크기를 현재 화면의 픽셀 크기로 다시 변환한다.
            self.square.size = (self.square_size, self.square_size)
            self.frame_size = frame_size
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

        self.win = win
        self.frame_size = None
        self.theme = NBACK_UI
        self.header = SharpText(
            win, height=0.038, pos=(0, 0.425), wrapWidth=1.2)
        y = self.theme["feedback_y"]
        self.panels = [visual.Rect(
            win, width=0.55, height=self.theme["feedback_panel_height"], pos=(x, y),
            fillColor=self.theme["panel"], lineColor=self.theme["border"], autoLog=False
        ) for x in (-0.30, 0.30)]
        self.labels = [SharpText(
            win, text=f"{NBACK[key].upper()}  /  {label}", height=0.026,
            pos=(x, y + 0.040), color=self.theme["muted"]
        ) for x, key, label in ((-.30, "visual_key", "Visual"), (.30, "auditory_key", "Auditory"))]
        self.visual = SharpText(
            win, height=self.theme["feedback_height"], pos=(-0.30, y - 0.020),
            wrapWidth=0.53)
        self.auditory = SharpText(
            win, height=self.theme["feedback_height"], pos=(0.30, y - 0.020),
            wrapWidth=0.53)

    def prepare(self, headers):
        for text in headers:
            self.header.prepare(text, self.theme["text"])
        for stimulus in (self.visual, self.auditory):
            stimulus.prepare("Correct", self.theme["correct"])
            stimulus.prepare("Incorrect", self.theme["incorrect"])
        for label in self.labels:
            label.prepare(label.text, self.theme["muted"])

    def draw(self, header, current):
        self.header.text = header
        self.header.color = self.theme["text"]
        self.header.draw()
        frame_size = tuple(self.win.size)
        if frame_size != self.frame_size:
            # 고정된 박스도 글자와 같은 화면 크기를 사용해야 서로 어긋나지 않는다.
            for panel, x in zip(self.panels, (-0.30, 0.30)):
                panel.pos = (x, self.theme["feedback_y"])
                panel.size = (0.55, self.theme["feedback_panel_height"])
            self.frame_size = frame_size
        for modality, panel, label in zip(
            ("visual", "auditory"), self.panels, self.labels
        ):
            panel.draw()
            label.draw()
            result = current.get(modality, "")
            color = self.theme["correct"] if result == "Correct" else self.theme["incorrect"]
            stimulus = getattr(self, modality)
            stimulus.text, stimulus.color = result, color
            stimulus.draw()
