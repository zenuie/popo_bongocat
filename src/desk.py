"""The desk: a keyboard (rotated 180, as seen from Po's side) + a mouse.
Fixed in place — Po reaches over to press them. Also resolves a key/mouse
press to a window-space target the hands aim for.
"""
from PySide6.QtCore import QRect
from PySide6.QtGui import QRegion, QTransform

from . import config
from .keyboard import KeyboardGraphic
from .mouse import MouseGraphic


class Desk:
    def __init__(self) -> None:
        self.keyboard = KeyboardGraphic()
        self.mouse = MouseGraphic()
        self._mask = QRegion(QRect(*config.KEYBOARD_RECT)).united(
            QRegion(QRect(*config.MOUSE_RECT))
        )

    # ---- lighting (visual feedback) ----
    def press_key(self, token: str) -> None:
        self.keyboard.press(token)

    def press_mouse(self, button: str) -> None:
        self.mouse.press(button)

    def scroll(self) -> None:
        self.mouse.scroll()

    # ---- targets for the hands (window coords) ----
    def key_target(self, token: str):
        c = self.keyboard.key_center(token)
        if c is None:
            return None
        wx, wy = config.rotate_point(*c)
        side = "left" if wx < config.DESK_ROT_CENTER[0] else "right"
        return (wx, wy, side)

    def mouse_target(self):
        x, y, w, h = config.MOUSE_RECT
        cx = x + w * 0.5
        side = "left" if cx < config.DESK_ROT_CENTER[0] else "right"
        return (cx, y + h * 0.5, side)

    # ---- per-frame ----
    def update(self) -> None:
        self.keyboard.update()
        self.mouse.update()

    def draw(self, painter) -> None:
        self._draw_rotated(painter, config.DESK_ROT_CENTER, self.keyboard.draw)
        mx, my, mw, mh = config.MOUSE_RECT
        self._draw_rotated(painter, (mx + mw / 2, my + mh / 2), self.mouse.draw)

    @staticmethod
    def _draw_rotated(painter, center, draw_fn) -> None:
        cx, cy = center
        painter.save()
        t = QTransform()
        t.translate(cx, cy)
        t.rotate(180)
        t.translate(-cx, -cy)
        painter.setWorldTransform(t, combine=True)
        draw_fn(painter)
        painter.restore()

    def mask_region(self) -> QRegion:
        return self._mask
