"""Global keyboard / mouse listener — the 'Bongo Cat' driver.

Uses pynput on a background thread and re-emits events as Qt signals (with the
key/button identity), which Qt delivers to the main thread via a queued
connection. Degrades gracefully: if pynput is missing or the OS denies input
monitoring, Po still runs — it just won't react to other apps.
"""
import sys

from PySide6.QtCore import QObject, Signal

try:
    from pynput import keyboard, mouse
    _HAS_PYNPUT = True
except Exception:  # pragma: no cover - import guard
    keyboard = mouse = None
    _HAS_PYNPUT = False


class GlobalInputListener(QObject):
    keyPressed = Signal(str)      # normalized token: char or special name
    mousePressed = Signal(str)    # 'left' / 'right' / 'middle'
    mouseScrolled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._kb = None
        self._ms = None

    @property
    def available(self) -> bool:
        return _HAS_PYNPUT

    @staticmethod
    def _warmup_macos() -> None:
        """Resolve the accessibility-trust call once on the main thread, so the
        keyboard and mouse listener threads don't race the (non-thread-safe)
        pyobjc lazy import of AXIsProcessTrusted and kill one of themselves."""
        if sys.platform != "darwin":
            return
        try:
            import HIServices
            HIServices.AXIsProcessTrusted()
        except Exception:
            pass

    def start(self) -> bool:
        if not _HAS_PYNPUT:
            return False
        self._warmup_macos()
        try:
            self._kb = keyboard.Listener(on_press=self._on_key)
            self._ms = mouse.Listener(
                on_click=self._on_click, on_scroll=self._on_scroll
            )
            # Start staggered (each .wait()s until running) so their startup
            # AXIsProcessTrusted checks don't run concurrently.
            self._kb.start()
            self._kb.wait()
            self._ms.start()
            self._ms.wait()
            return True
        except Exception:
            self._kb = self._ms = None
            return False

    @staticmethod
    def _token(key) -> str:
        name = getattr(key, "name", None)        # special keys (Key.space, ...)
        if name:
            return name
        char = getattr(key, "char", None)        # character keys (KeyCode)
        if char:
            return char.lower()
        return ""

    def _on_key(self, key) -> None:
        token = self._token(key)
        if token:
            self.keyPressed.emit(token)

    def _on_click(self, _x, _y, button, pressed) -> None:
        if pressed:
            self.mousePressed.emit(getattr(button, "name", "left"))

    def _on_scroll(self, _x, _y, _dx, _dy) -> None:
        self.mouseScrolled.emit()

    def stop(self) -> None:
        for listener in (self._kb, self._ms):
            if listener is not None:
                try:
                    listener.stop()
                except Exception:
                    pass
        self._kb = self._ms = None
