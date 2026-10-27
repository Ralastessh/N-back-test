"""macOS 기본 전체화면 버튼과 PsychoPy의 화면 크기를 함께 관리한다."""

import sys


def enable_native_fullscreen(win):
    if sys.platform != "darwin" or win.fullscr:
        return False
    if win.winType != "pyglet":
        raise RuntimeError("Native macOS fullscreen requires PsychoPy's pyglet backend.")

    from pyglet.libs.darwin import cocoapy

    handle = win.backend.winHandle
    # pyglet가 소유한 창을 그대로 사용하고 다른 Objective-C wrapper로 감싸지 않는다.
    native = handle._nswindow
    native.setStyleMask_(native.styleMask() | cocoapy.NSResizableWindowMask)
    native.setCollectionBehavior_(
        native.collectionBehavior() | (1 << 7)  # NSWindowCollectionBehaviorFullScreenPrimary
    )
    native.standardWindowButton_(2).setEnabled_(True)  # NSWindowZoomButton
    handle._resizable = True

    # resize 콜백은 새 크기만 보관한다. 그릴 준비가 된 GL context에서 반영하여
    # 전체화면 전환 중 일시적인 0 크기와 framebuffer 불일치를 피한다.
    pending_size = None
    original_set_current = win.backend.setCurrent

    def on_resize(width, height):
        nonlocal pending_size
        if width > 0 and height > 0:
            pending_size = (width, height)
        return True

    def set_current():
        nonlocal pending_size
        changed = original_set_current()
        if pending_size is None:
            return changed
        pixels = handle.get_framebuffer_size()
        if min(pixels) <= 0:
            return changed
        win.clientSize[:] = pending_size
        win.backend._frameBufferSize[:] = pixels
        pending_size = None
        win.resetViewport()
        win.resetEyeTransform(clearDepth=False)
        return True

    def draw_waiting_screen():
        renderer = getattr(win, "_resize_draw", None)
        if renderer is None or handle.context is None:
            return False
        if min(handle.get_framebuffer_size()) <= 0:
            return False
        set_current()
        renderer()
        return True

    def on_expose():
        if draw_waiting_screen():
            # 크기 변경 후 다시 그릴 때 RT clock과 flip callback은 실행하지 않는다.
            handle.flip()
        return True

    win.backend.setCurrent = set_current
    handle.on_resize = on_resize
    handle.on_draw = draw_waiting_screen
    handle.on_expose = on_expose
    return True
