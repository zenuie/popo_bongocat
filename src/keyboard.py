"""A drawn QWERTY keyboard whose real key positions light up on input.

`press(token)` maps a normalized input token (a character, or a pynput
special-key name like 'space'/'shift') to a physical key id and lights that
key. Levels decay each frame. No art assets — pure QPainter.
"""
from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen

from . import config

# Each row is a list of (key_id, width_in_units). Every row totals 15 units;
# rows are scaled to a common pixel width so they line up.
KEY_ROWS = [
    [("grave", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1),
     ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("minus", 1), ("equal", 1),
     ("backspace", 2)],
    [("tab", 1.5), ("q", 1), ("w", 1), ("e", 1), ("r", 1), ("t", 1), ("y", 1),
     ("u", 1), ("i", 1), ("o", 1), ("p", 1), ("lbracket", 1), ("rbracket", 1),
     ("backslash", 1.5)],
    [("caps", 1.75), ("a", 1), ("s", 1), ("d", 1), ("f", 1), ("g", 1), ("h", 1),
     ("j", 1), ("k", 1), ("l", 1), ("semicolon", 1), ("quote", 1),
     ("enter", 2.25)],
    [("lshift", 2.25), ("z", 1), ("x", 1), ("c", 1), ("v", 1), ("b", 1),
     ("n", 1), ("m", 1), ("comma", 1), ("period", 1), ("slash", 1),
     ("rshift", 2.75)],
    [("lctrl", 1.25), ("lcmd", 1.25), ("lalt", 1.25), ("space", 6.25),
     ("ralt", 1.25), ("rcmd", 1.25), ("menu", 1.25), ("rctrl", 1.25)],
]


def _build_token_map():
    """Map every plausible input token to a physical key id."""
    token_map = {ch: ch for ch in "abcdefghijklmnopqrstuvwxyz0123456789"}
    symbol_pairs = {
        "grave": "`~", "minus": "-_", "equal": "=+", "lbracket": "[{",
        "rbracket": "]}", "backslash": "\\|", "semicolon": ";:", "quote": "'\"",
        "comma": ",<", "period": ".>", "slash": "/?",
    }
    for key_id, chars in symbol_pairs.items():
        for ch in chars:
            token_map[ch] = key_id
    token_map.update({"!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
                      "^": "6", "&": "7", "*": "8", "(": "9", ")": "0"})
    token_map.update({
        "space": "space", "enter": "enter", "return": "enter", "tab": "tab",
        "backspace": "backspace", "caps_lock": "caps",
        "shift": "lshift", "shift_l": "lshift", "shift_r": "rshift",
        "ctrl": "lctrl", "ctrl_l": "lctrl", "ctrl_r": "rctrl",
        "alt": "lalt", "alt_l": "lalt", "alt_r": "ralt", "alt_gr": "ralt",
        "cmd": "lcmd", "cmd_l": "lcmd", "cmd_r": "rcmd", "menu": "menu",
    })
    return token_map


class KeyboardGraphic:
    def __init__(self) -> None:
        self._chassis = config.KEYBOARD_RECT
        self._keys = self._build_keys()        # list of (key_id, QRectF)
        self._levels: dict[str, float] = {}     # key_id -> 0..1
        self._token_map = _build_token_map()
        self._centers = {kid: (r.center().x(), r.center().y()) for kid, r in self._keys}

    def key_center(self, token: str):
        """Unrotated (x, y) center of the key a token maps to, or None."""
        kid = self._token_map.get(token)
        return self._centers.get(kid) if kid is not None else None

    def _build_keys(self):
        x, y, w, _ = self._chassis
        pad = config.KEYBOARD_PAD
        inner_x = x + pad
        inner_y = y + pad
        inner_w = w - 2 * pad
        keys = []
        for r, row in enumerate(KEY_ROWS):
            ky = inner_y + r * (config.KEY_H + config.ROW_GAP)
            unit = (inner_w - (len(row) - 1) * config.KEY_GAP) / 15.0
            kx = inner_x
            for key_id, units in row:
                kw = units * unit
                keys.append((key_id, QRectF(kx, ky, kw, config.KEY_H)))
                kx += kw + config.KEY_GAP
        return keys

    def press(self, token: str) -> None:
        key_id = self._token_map.get(token)
        if key_id is not None:
            self._levels[key_id] = 1.0

    def update(self) -> None:
        decay = config.KEY_DECAY_PER_FRAME
        self._levels = {
            key_id: level * decay
            for key_id, level in self._levels.items()
            if level * decay >= 0.01
        }

    def is_animating(self) -> bool:
        """True while any key is still lit (and thus needs redrawing)."""
        return bool(self._levels)

    def draw(self, p) -> None:
        x, y, w, h = self._chassis
        p.setPen(QPen(QColor(config.COLOR_OUTLINE), 1.5))
        p.setBrush(QBrush(QColor(config.COLOR_CHASSIS)))
        p.drawRoundedRect(QRectF(x, y, w, h), 7, 7)

        base = QColor(config.COLOR_KEY)
        active = QColor(config.COLOR_KEY_ACTIVE)
        for key_id, rect in self._keys:
            level = self._levels.get(key_id, 0.0)
            key = QRectF(rect).translated(0, config.KEY_DIP * level)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(_lerp_color(base, active, level)))
            p.drawRoundedRect(key, 2.5, 2.5)
            if level > 0.05:
                glow = QColor(active)
                glow.setAlphaF(0.4 * level)
                p.setPen(QPen(glow, 1.5))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(key.adjusted(-1, -1, 1, 1), 3, 3)

    def bounds(self) -> QRect:
        x, y, w, h = self._chassis
        return QRect(int(x), int(y), int(w), int(h))


def _lerp_color(a: QColor, b: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
    )
