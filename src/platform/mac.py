"""macOS-specific hooks (Phase 2 — unused by the MVP).

Intended future use: a fully click-through 'ghost' mode via PyObjC
(`NSWindow.setIgnoresMouseEvents_(True)`), and hiding the Dock icon
(LSUIElement) when packaged as a .app.
"""


def set_ghost_mode(window, enabled: bool) -> None:
    raise NotImplementedError("macOS ghost mode is a Phase 2 feature.")
