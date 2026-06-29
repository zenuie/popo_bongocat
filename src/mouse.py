"""A drawn mouse with separate left button, right button and scroll wheel.

`press('left'|'right'|'middle')` lights the matching part; `scroll()` lights
the wheel. Levels decay each frame. Pure QPainter, no art assets.
"""
from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen

from . import config

from .keyboard import _lerp_color  # shared color helper


class MouseGraphic:
    def __init__(self) -> None:
        self._rect = config.MOUSE_RECT
        self._left = 0.0
        self._right = 0.0
        self._wheel = 0.0

    def press(self, button: str) -> None:
        if button == "left":
            self._left = 1.0
        elif button == "right":
            self._right = 1.0
        elif button == "middle":
            self._wheel = 1.0

    def scroll(self) -> None:
        self._wheel = 1.0

    def update(self) -> None:
        decay = config.MOUSE_DECAY_PER_FRAME
        self._left = self._left * decay if self._left * decay >= 0.01 else 0.0
        self._right = self._right * decay if self._right * decay >= 0.01 else 0.0
        self._wheel = self._wheel * decay if self._wheel * decay >= 0.01 else 0.0

    def is_animating(self) -> bool:
        """True while any button/wheel is still lit (and thus needs redrawing)."""
        return self._left > 0.0 or self._right > 0.0 or self._wheel > 0.0

    def draw(self, p) -> None:
        x, y, w, h = self._rect
        dip = config.KEY_DIP * 0.5 * max(self._left, self._right, self._wheel)
        top = y + dip
        body = QRectF(x, top, w, h)
        radius_x, radius_y = w * 0.45, w * 0.42

        base = QColor(config.COLOR_MOUSE)
        active = QColor(config.COLOR_ACTIVE)

        path = QPainterPath()
        path.addRoundedRect(body, radius_x, radius_y)

        # Fill body + light up pressed buttons, clipped to the rounded shape.
        p.save()
        p.setClipPath(path)
        p.fillRect(body, base)
        midx = x + w / 2
        btn_h = h * 0.42
        if self._left > 0.02:
            p.fillRect(QRectF(x, top, w / 2, btn_h),
                       _lerp_color(base, active, 0.9 * self._left))
        if self._right > 0.02:
            p.fillRect(QRectF(midx, top, w / 2, btn_h),
                       _lerp_color(base, active, 0.9 * self._right))
        p.restore()

        # Scroll wheel (between the buttons).
        wheel_col = _lerp_color(QColor(config.COLOR_WHEEL), active, self._wheel)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(wheel_col))
        p.drawRoundedRect(QRectF(midx - 2.5, top + 7, 5, 12), 2.5, 2.5)

        # Button divider lines.
        p.setPen(QPen(QColor(config.COLOR_MOUSE_LINE), 1.2))
        p.drawLine(QPointF(x + 3, top + btn_h), QPointF(x + w - 3, top + btn_h))
        p.drawLine(QPointF(midx, top + btn_h - 3), QPointF(midx, top + btn_h))

        # Outline on top.
        p.setPen(QPen(QColor(config.COLOR_OUTLINE), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(body, radius_x, radius_y)

    def bounds(self) -> QRect:
        x, y, w, h = self._rect
        return QRect(int(x), int(y), int(w), int(h + 3))
