"""두 Span 검사의 공통 텍스트 안내와 계속/중단 키 처리."""


def show(win, text):
    from psychopy import visual

    def draw():
        visual.TextStim(win, text=text, height=0.035, wrapWidth=1.1).draw()

    # 키를 기다리는 동안에도 창 크기가 바뀌면 같은 내용을 다시 그린다.
    win._resize_draw = draw
    draw()
    return win.flip()


def pause(win, text, kb):
    show(win, text + "\n\nSPACE: continue | ESC: quit")
    keys = kb.waitKeys(keyList=["space", "escape"], waitRelease=False)
    if any(k.name == "escape" for k in keys):
        raise KeyboardInterrupt
