"""Persistent user settings: global scale, active skin, follow-mouse toggle.

Stored as JSON in the platform's per-user config dir. Reads/writes are
defensive — a missing or corrupt file falls back to defaults, and an
unwritable location is tolerated (settings just won't persist).
"""
import json
import os
import sys

APP_DIR_NAME = "PoBongoCat"

SCALE_MIN = 0.5
SCALE_MAX = 2.0

DEFAULTS = {
    "scale": 1.0,
    "skin": "default",
    "follow_mouse": True,
}


def config_dir() -> str:
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, APP_DIR_NAME)


def settings_path() -> str:
    return os.environ.get("PO_SETTINGS_PATH") or os.path.join(config_dir(), "settings.json")


def _sanitize(data: dict) -> dict:
    out = dict(DEFAULTS)
    try:
        out["scale"] = min(SCALE_MAX, max(SCALE_MIN, float(data.get("scale", 1.0))))
    except (TypeError, ValueError):
        out["scale"] = DEFAULTS["scale"]
    skin = data.get("skin", "default")
    out["skin"] = skin if isinstance(skin, str) and skin else "default"
    out["follow_mouse"] = bool(data.get("follow_mouse", True))
    return out


def load() -> dict:
    try:
        with open(settings_path(), encoding="utf-8") as f:
            stored = json.load(f)
    except (OSError, ValueError):
        stored = {}
    if not isinstance(stored, dict):
        stored = {}
    return _sanitize(stored)


def save(**changes) -> dict:
    """Merge `changes` into the stored settings and persist. Returns the merged
    settings (so callers see the sanitized result even if the write fails)."""
    merged = _sanitize({**load(), **changes})
    try:
        os.makedirs(os.path.dirname(settings_path()), exist_ok=True)
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
    except OSError:
        pass
    return merged
