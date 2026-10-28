import sys
from pyglet.libs.darwin import cocoapy

def enable_native_fullscreen(win):
    if sys.platform != "darwin" or win.fullscr:
        return False
    if win.winType != "pyglet":
        raise RuntimeError("Native macOS fullscreen requires PsychoPy's pyglet backend.")

    handle = win.backend.winHandle
    native = handle._nswindow
    native.setStyleMask_(native.styleMask() | cocoapy.NSResizableWindowMask)
    native.setCollectionBehavior_(
        native.collectionBehavior() | (1 << 7)  # NSWindowCollectionBehaviorFullScreenPrimary
    )
    native.standardWindowButton_(2).setEnabled_(True)  # NSWindowZoomButton
    handle._resizable = True
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
            handle.flip()
        return True

    win.backend.setCurrent = set_current
    handle.on_resize = on_resize
    handle.on_draw = draw_waiting_screen
    handle.on_expose = on_expose
    return True
