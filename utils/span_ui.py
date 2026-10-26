"""PsychoPy 화면·키보드 보조 함수. 단어 회상은 한글 IME를 위한 PsychoPy GUI 입력창(Qt/wx) 사용."""


def show(win, text):
    from psychopy import visual

    visual.TextStim(win, text=text, height=0.035, wrapWidth=1.1).draw()
    return win.flip()


def pause(win, text, kb):
    show(win, text + "\n\nSPACE: continue | ESC: quit")
    keys = kb.waitKeys(keyList=["space", "escape"], waitRelease=False)
    if any(k.name == "escape" for k in keys):
        raise KeyboardInterrupt


def wait_until(clock, deadline, kb):
    from psychopy import core

    while clock.getTime() < deadline:
        if kb.getKeys(keyList=["escape"], waitRelease=False):
            raise KeyboardInterrupt
        core.wait(0.001)


def recall_digits(win, kb):
    from psychopy import core

    clock = core.Clock()
    win.callOnFlip(kb.clearEvents)
    win.callOnFlip(kb.clock.reset)
    win.callOnFlip(clock.reset)
    show(
        win, "Type the digits in the requested order.\nBACKSPACE: edit | ENTER: submit"
    )
    response = []
    events = []
    while True:
        for key in kb.getKeys(waitRelease=False, clear=True):
            events.append(dict(key=key.name, rt=key.rt))
            if key.name == "escape":
                raise KeyboardInterrupt
            if key.name in ("return", "num_enter"):
                return response, key.rt, events
            if key.name == "backspace":
                response = response[:-1]
            elif key.name in list("123456789"):
                response.append(key.name)
            show(win, " ".join(response) + "\n\nENTER: submit | BACKSPACE: edit")
        core.wait(0.001)


def recall_words(win):
    from psychopy import gui, core

    clock = core.Clock()
    win.callOnFlip(clock.reset)
    show(
        win,
        "Recall the final words in order.\nSeparate words with spaces. Enter _ for each missing position.",
    )
    dialog = gui.Dlg(title="Serial word recall")
    dialog.addField("Words (spaces between words; _ for a missing word):", "")
    values = dialog.show()
    if not dialog.OK:
        raise KeyboardInterrupt
    response = values[0].strip().split()
    return response, clock.getTime()
