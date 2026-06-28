"""Po's two gloved hands, controlled entirely by the program.

Each hand eases toward a target (a pressed key, or the mouse, or its rest spot
on the keyboard), taps down on activation, and drifts back to rest when idle.
A simple cream sleeve is drawn from the (hidden, behind-keyboard) shoulder to
the glove so the arm reads as connected. Perfect registration, no jitter.
"""
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF

from . import config


class _Hand:
    def __init__(self, rest, shoulder) -> None:
        self.rest = rest
        self.shoulder = shoulder
        self.x, self.y = float(rest[0]), float(rest[1])
        self.tx, self.ty = float(rest[0]), float(rest[1])
        self.tap = 0.0
        self.last_active = -1e9

    def activate(self, target, now) -> None:
        self.tx = float(target[0])
        self.ty = max(float(target[1]), config.HAND_TIP_Y_MIN)  # keep off Po's face
        self.tap = 1.0
        self.last_active = now

    def update(self, now) -> None:
        if now - self.last_active > config.HAND_RETURN_MS / 1000.0:
            self.tx, self.ty = float(self.rest[0]), float(self.rest[1])
        self.x += (self.tx - self.x) * config.HAND_EASE
        self.y += (self.ty - self.y) * config.HAND_EASE
        self.tap *= config.HAND_DECAY_PER_FRAME
        if self.tap < 0.02:
            self.tap = 0.0


class Hands:
    def __init__(self, glove_pixmap) -> None:
        self.glove = glove_pixmap
        self._gw = glove_pixmap.width() * config.HAND_SCALE
        self._gh = glove_pixmap.height() * config.HAND_SCALE
        self.left = _Hand(config.LEFT_REST, config.LEFT_SHOULDER)
        self.right = _Hand(config.RIGHT_REST, config.RIGHT_SHOULDER)

    def press_key(self, side: str, target, now) -> None:
        (self.left if side == "left" else self.right).activate(target, now)

    def update(self, now) -> None:
        self.left.update(now)
        self.right.update(now)

    # ---- drawing ----
    def draw(self, painter, lean_x: float = 0.0) -> None:
        self._draw_one(painter, self.right, True, lean_x)
        self._draw_one(painter, self.left, False, lean_x)

    def _draw_one(self, p, hand, mirror, lean_x) -> None:
        tip_x = hand.x
        tip_y = hand.y + config.HAND_TAP_DIP * hand.tap
        shoulder = (hand.shoulder[0] + lean_x, hand.shoulder[1])
        wrist = (tip_x, tip_y - self._gh * 0.5)
        self._draw_sleeve(p, shoulder, wrist)

        gw, gh = self._gw, self._gh
        x = tip_x - config.HAND_TIP_FX * gw
        y = tip_y - config.HAND_TIP_FY * gh
        pm = self.glove
        if mirror:
            p.save()
            p.translate(x + gw, y)
            p.scale(-1, 1)
            p.drawPixmap(QRectF(0, 0, gw, gh), pm, QRectF(0, 0, pm.width(), pm.height()))
            p.restore()
        else:
            p.drawPixmap(QRectF(x, y, gw, gh), pm, QRectF(0, 0, pm.width(), pm.height()))

    @staticmethod
    def _draw_sleeve(p, shoulder, wrist) -> None:
        sx, sy = shoulder
        wx, wy = wrist
        dx, dy = wx - sx, wy - sy
        n = (dx * dx + dy * dy) ** 0.5 or 1.0
        nx, ny = -dy / n, dx / n
        hs, hw = config.SLEEVE_HW_SHOULDER, config.SLEEVE_HW_WRIST
        quad = QPolygonF([
            QPointF(sx + nx * hs, sy + ny * hs),
            QPointF(wx + nx * hw, wy + ny * hw),
            QPointF(wx - nx * hw, wy - ny * hw),
            QPointF(sx - nx * hs, sy - ny * hs),
        ])
        pen = QPen(QColor(config.COLOR_SLEEVE_LINE), 3)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(QBrush(QColor(config.COLOR_SLEEVE)))
        p.drawPolygon(quad)
        p.setPen(QPen(QColor(config.COLOR_SLEEVE_LINE), 1.4))
        for f in (0.55, 0.74):
            cx, cy = sx + dx * f, sy + dy * f
            w = (hs + (hw - hs) * f) * 0.85
            p.drawLine(QPointF(cx - nx * w, cy - ny * w), QPointF(cx + nx * w, cy + ny * w))
