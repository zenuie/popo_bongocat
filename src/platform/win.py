"""Windows-specific hooks (Phase 2 — unused by the MVP).

Intended future use: a fully click-through 'ghost' mode via the extended
window styles WS_EX_LAYERED | WS_EX_TRANSPARENT (ctypes / pywin32).
"""


def set_ghost_mode(window, enabled: bool) -> None:
    raise NotImplementedError("Windows ghost mode is a Phase 2 feature.")
