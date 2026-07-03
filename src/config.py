"""Central tuning constants for Po. Tweak the handfeel / layout here."""
from . import settings as _settings

# --- User settings (issues #4/#5). All geometry below is authored at scale
#     1.0; PET_SCALE is applied as one paint transform in the window, so these
#     constants never need to be rescaled individually. PET_SCALE is mutated
#     live by PetWindow.set_scale(). ---
_loaded = _settings.load()
PET_SCALE = _loaded["scale"]
ACTIVE_SKIN = _loaded["skin"]
FOLLOW_MOUSE = _loaded["follow_mouse"]

# --- Scene canvas: Po (body) behind, keyboard + mouse on the desk, hands in front ---
CANVAS_WIDTH = 372
CANVAS_HEIGHT = 249

# --- Po body (static art: assets/parts/po_body.png) ---
PO_BODY_SCALE = 0.31
PO_BODY_TOP = 6           # y of the body's top edge
PO_CENTER_X = 209         # centered over the keyboard

# --- Frame loop ---
FPS = 60
FRAME_INTERVAL_MS = max(1, round(1000 / FPS))

# --- Idle floating (breathing) + small body nod on activity ---
FLOAT_AMPLITUDE = 5.0
FLOAT_PERIOD = 3.2
IMPULSE_HALF_LIFE = 0.10
NOD_DIP = 3.0             # px the body dips on a keystroke

# --- Hands (program-controlled gloves: assets/parts/po_hand.png) ---
HAND_SCALE = 0.31
LEFT_REST = (157, 164)
RIGHT_REST = (261, 164)
LEFT_SHOULDER = (154, 112)     # visible body-side anchors; arms extend from Po
RIGHT_SHOULDER = (264, 112)
HAND_TAP_DIP = 6.0            # px a hand presses down on a tap
HAND_EASE = 0.42             # how fast a hand moves toward its target (0..1)
HAND_RETURN_MS = 600         # idle gap before a hand drifts back to rest
HAND_IMPULSE_HALF_LIFE = 0.07
HAND_TIP_Y_MIN = 162         # never let a hand ride up above this (keeps off the face)
# glove fingertip in sprite space (fraction of sprite w/h) — the press point
HAND_TIP_FX = 0.50
HAND_TIP_FY = 0.90
# sleeve endpoint in sprite space (fraction of sprite w/h). Defaults to the old
# `tip_y - glove_height * 0.5` position: 0.90 - 0.50 = 0.40.
HAND_WRIST_FX = 0.50
HAND_WRIST_FY = 0.40
# sleeve (drawn forearm) half-widths at shoulder / wrist
SLEEVE_HW_SHOULDER = 9.0
SLEEVE_HW_WRIST = 14.0

# --- Body lean: Po leans toward what its active hand is reaching (shortens the
#     arm to a far target like the mouse, and adds life) ---
BODY_LEAN_FACTOR = 0.45      # fraction of (target_x - center) the body leans
BODY_LEAN_MAX = 30           # px max lean
BODY_LEAN_EASE = 0.16

# --- Desk geometry (keyboard high enough to hide the body's band behind it) ---
KEYBOARD_RECT = (70, 124, 278, 99)   # chassis x, y, w, h
KEYBOARD_PAD = 6
KEY_GAP = 2
KEY_H = 15
ROW_GAP = 3
KEY_DIP = 2.0
KEY_PRESS_HALF_LIFE = 0.07
DESK_ROT_CENTER = (209, 173.5)       # keyboard rotated 180 about its own center

MOUSE_RECT = (14, 162, 40, 54)       # left of the keyboard, rotated 180; Po reaches it
MOUSE_PRESS_HALF_LIFE = 0.09

# --- Interaction timing ---
DRAG_THRESHOLD = 5
REACTION_THROTTLE_S = 0.018          # min seconds between body nods

# --- Mouse-follow (issue #3): the desk mouse echoes the real cursor as a small,
#     scaled-down wiggle, and the near hand rests on it while the cursor moves ---
MOUSE_FOLLOW_RANGE_X = 18.0          # px the desk mouse can drift horizontally
MOUSE_FOLLOW_RANGE_Y = 9.0           # px vertically
MOUSE_FOLLOW_EASE = 0.18             # how fast the offset eases toward target
MOUSE_FOLLOW_IDLE_MS = 700           # cursor-still gap before the hand lets go

# --- Palette (matches Po: orange accents on charcoal) ---
COLOR_CHASSIS = "#26262B"
COLOR_KEY = "#3B3B43"
COLOR_KEY_ACTIVE = "#F2742F"
COLOR_OUTLINE = "#141418"
COLOR_MOUSE = "#2C2C32"
COLOR_MOUSE_LINE = "#141418"
COLOR_ACTIVE = "#F2742F"
COLOR_WHEEL = "#5A5A63"
COLOR_SLEEVE = "#F3EEE4"             # cream sleeve drawn between body and glove
COLOR_SLEEVE_LINE = "#141418"

# --- Assets ---
ASSET_DIR = "assets"


def asset_path(name: str) -> str:
    return f"{ASSET_DIR}/{name}"


def rotate_point(x: float, y: float):
    """180-degree rotation about the desk center (for the rotated keyboard)."""
    cx, cy = DESK_ROT_CENTER
    return (2 * cx - x, 2 * cy - y)


def _per_frame_decay(half_life: float) -> float:
    dt = FRAME_INTERVAL_MS / 1000.0
    return 0.5 ** (dt / half_life) if half_life > 0 else 0.0


KEY_DECAY_PER_FRAME = _per_frame_decay(KEY_PRESS_HALF_LIFE)
MOUSE_DECAY_PER_FRAME = _per_frame_decay(MOUSE_PRESS_HALF_LIFE)
HAND_DECAY_PER_FRAME = _per_frame_decay(HAND_IMPULSE_HALF_LIFE)
