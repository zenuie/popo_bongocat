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

from . import settings
from .config import asset_path
from .resources import resource_path

BODY_FILE = "po_body.png"
HAND_FILE = "po_hand.png"
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
