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
        self.fixation = visual.TextStim(win, text="+", height=0.035)

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

        self.header = visual.TextStim(win, height=0.025, pos=(0, 0.43), wrapWidth=1.2)
        self.visual = visual.TextStim(
            win, height=0.022, pos=(-0.30, -0.35), wrapWidth=0.60
        )
        self.auditory = visual.TextStim(
            win, height=0.022, pos=(0.30, -0.35), wrapWidth=0.60
        )
        self.previous = visual.TextStim(
            win, height=0.018, pos=(0, -0.44), wrapWidth=1.25
        )
        self.cache = {}

    def update(self, stimulus, text, color="white"):
        value = (text, color)
        if self.cache.get(id(stimulus)) != value:
            stimulus.text = text
            stimulus.color = color
            self.cache[id(stimulus)] = value
        if text:
            stimulus.draw()

    def draw(self, header, current, previous=""):
        self.update(self.header, header)
        for modality in ("visual", "auditory"):
            text = current.get(modality, "")
            color = "lime" if text.startswith("Correct") else "salmon"
            self.update(
                getattr(self, modality),
                f"{modality.title()}: {text}" if text else "",
                color,
            )
        self.update(self.previous, previous)
