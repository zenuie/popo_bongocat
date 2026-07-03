"""Character skins (issue #5).

A skin is just a folder holding the two art parts Po renders — ``po_body.png``
and ``po_hand.png`` — since the keyboard and mouse are drawn procedurally and
are skin-independent. The built-in "default" skin is the bundled Po art.

Skins are discovered from two places:
  * bundled:  <app>/assets/skins/<name>/
  * user:     <config_dir>/skins/<name>/      (drop your own in here)

The layout (hand rest spots, tip fractions, etc.) is shared, so a custom skin
should be cut to roughly the same proportions as Po — see docs/skins.md.
"""
import os
import json

from . import config, settings
from .config import asset_path
from .resources import resource_path

BODY_FILE = "po_body.png"
HAND_FILE = "po_hand.png"
META_FILE = "skin.json"
DEFAULT = "default"


def user_skins_dir() -> str:
    return os.path.join(settings.config_dir(), "skins")


def _bundled_skins_dir() -> str:
    return resource_path(asset_path("skins"))


def _is_skin_folder(folder: str) -> bool:
    return (os.path.isfile(os.path.join(folder, BODY_FILE))
            and os.path.isfile(os.path.join(folder, HAND_FILE)))


def available_skins() -> list[str]:
    """The default skin plus every valid skin folder found, de-duplicated."""
    names = [DEFAULT]
    seen = {DEFAULT}
    for base in (_bundled_skins_dir(), user_skins_dir()):
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            folder = os.path.join(base, name)
            if name not in seen and os.path.isdir(folder) and _is_skin_folder(folder):
                names.append(name)
                seen.add(name)
    return names


def skin_assets(name: str) -> "tuple[str, str] | None":
    """(body_path, hand_path) for `name`, or None if it can't be resolved
    (caller should fall back to the default skin)."""
    if name == DEFAULT:
        return (resource_path(asset_path(f"parts/{BODY_FILE}")),
                resource_path(asset_path(f"parts/{HAND_FILE}")))
    for base in (user_skins_dir(), _bundled_skins_dir()):
        folder = os.path.join(base, name)
        if _is_skin_folder(folder):
            return (os.path.join(folder, BODY_FILE), os.path.join(folder, HAND_FILE))
    return None


def user_skin_folder(name: str) -> "str | None":
    if name == DEFAULT:
        return None
    folder = os.path.join(user_skins_dir(), name)
    return folder if _is_skin_folder(folder) else None


def writable_skin_meta_path(name: str) -> "str | None":
    folder = user_skin_folder(name)
    if folder is None:
        return None
    return os.path.join(folder, META_FILE)


def default_hand_layout() -> dict[str, tuple[float, float]]:
    return {
        "tip": (config.HAND_TIP_FX, config.HAND_TIP_FY),
        "wrist": (config.HAND_WRIST_FX, config.HAND_WRIST_FY),
    }


def skin_hand_layout(name: str) -> dict[str, tuple[float, float]]:
    """Resolve optional hand anchor metadata for a skin.

    `skin.json` may contain:
      {"hand_tip": [0.5, 0.9], "hand_wrist": [0.5, 0.4]}

    Values are fractions of po_hand.png width/height and are clamped to the
    sprite bounds. Missing or invalid metadata falls back to the default layout.
    """
    layout = default_hand_layout()
    if name == DEFAULT:
        return layout
    meta_path = None
    for base in (user_skins_dir(), _bundled_skins_dir()):
        folder = os.path.join(base, name)
        candidate = os.path.join(folder, META_FILE)
        if _is_skin_folder(folder) and os.path.isfile(candidate):
            meta_path = candidate
            break
    if meta_path is None:
        return layout
    try:
        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
    except (OSError, ValueError):
        return layout

    tip = _point_from_meta(meta.get("hand_tip"))
    wrist = _point_from_meta(meta.get("hand_wrist"))
    if tip is not None:
        layout["tip"] = tip
    if wrist is not None:
        layout["wrist"] = wrist
    return layout


def _point_from_meta(value) -> "tuple[float, float] | None":
    if not isinstance(value, list | tuple) or len(value) != 2:
        return None
    try:
        x, y = float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None
    return (_clamp01(x), _clamp01(y))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def save_skin_hand_layout(name: str, layout: dict[str, tuple[float, float]]) -> bool:
    path = writable_skin_meta_path(name)
    if path is None:
        return False
    tip = layout.get("tip")
    wrist = layout.get("wrist")
    tip = _point_from_meta(tip)
    wrist = _point_from_meta(wrist)
    if tip is None or wrist is None:
        return False
    data = {
        "hand_tip": [tip[0], tip[1]],
        "hand_wrist": [wrist[0], wrist[1]],
    }
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
    except OSError:
        return False
    return True
