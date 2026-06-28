"""Platform seam.

The MVP is fully cross-platform (Qt + setMask), so this is a no-op. Native
extras — a fully click-through 'ghost' mode, or hiding the Dock/taskbar icon —
belong here in Phase 2; see win.py / mac.py for the intended hooks.

Named `platform` to match PLAN.md §4. It is a *subpackage* (src.platform), so
it never shadows the standard library `platform` module as long as the app is
launched as a package (`python -m src.main`).
"""


def apply_platform_tweaks(window) -> None:  # noqa: ARG001 - Phase 2 seam
    return
