"""macOS 기본 전체화면 버튼과 PsychoPy의 화면 크기를 함께 관리한다."""

import sys


def enable_native_fullscreen(win):
    if sys.platform != "darwin" or win.fullscr:
        return False
    if win.winType != "pyglet":
        raise RuntimeError("Native macOS fullscreen requires PsychoPy's pyglet backend.")

    import AppKit
    from ctypes import c_void_p

    handle = win.backend.winHandle
    native = AppKit.NSWindow(c_void_p=handle._nswindow.ptr)
    native.setStyleMask_(native.styleMask() | AppKit.NSWindowStyleMaskResizable)
    native.setCollectionBehavior_(
        native.collectionBehavior() | AppKit.NSWindowCollectionBehaviorFullScreenPrimary
    )
    native.standardWindowButton_(AppKit.NSWindowZoomButton).setEnabled_(True)
    handle._resizable = True

    original_resize = win.backend.onResize

    def on_resize(width, height):
        original_resize(width, height)
        win.clientSize[:] = (width, height)
        view = handle.context._nscontext.view()
        bounds = view.convertRectToBacking_(view.bounds()).size
        pixels = (int(bounds.width), int(bounds.height))
        win.backend._frameBufferSize[:] = pixels
        win.viewport = win.scissor = (0, 0, *pixels)
        win.resetEyeTransform()

    handle.on_resize = on_resize
    return True
