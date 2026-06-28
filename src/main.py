"""Entry point. Run from the project root with:  python -m src.main"""
import sys

from PySide6.QtWidgets import QApplication

from .input_listener import GlobalInputListener
from .pet_window import PetWindow
from .platform import apply_platform_tweaks
from .tray import build_tray

_PERMISSION_HINT = (
    "[Po] Global input listening is unavailable, so Po won't react to typing/"
    "clicks in other apps (it still runs).\n"
    "      macOS: grant Input Monitoring + Accessibility to your terminal "
    "(or Python) in System Settings > Privacy & Security, then relaunch."
)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Po")
    app.setApplicationDisplayName("Po")
    app.setQuitOnLastWindowClosed(False)

    window = PetWindow()
    apply_platform_tweaks(window)
    window.show()

    tray = build_tray(app, window)

    listener = GlobalInputListener()
    listener.keyPressed.connect(window.on_key)
    listener.mousePressed.connect(window.on_mouse_button)
    listener.mouseScrolled.connect(window.on_scroll)
    if not listener.start():
        print(_PERMISSION_HINT, file=sys.stderr)
    app.aboutToQuit.connect(listener.stop)

    # keep references alive for the app's lifetime
    window._tray = tray            # type: ignore[attr-defined]
    window._listener = listener    # type: ignore[attr-defined]

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
