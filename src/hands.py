"""Po's two gloved hands, controlled entirely by the program.

Each hand eases toward a target (a pressed key, or the mouse, or its rest spot
on the keyboard), taps down on activation, and drifts back to rest when idle.
A simple cream sleeve is drawn from a body-side shoulder anchor to the glove so
the arm reads as connected. Perfect registration, no jitter.
"""
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF

from . import config
from .sprites import scale_for_display


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

    def track(self, target, now) -> None:
        """Rest on a moving target (the mouse) without the press-down dip."""
        self.tx = float(target[0])
        self.ty = max(float(target[1]), config.HAND_TIP_Y_MIN)
        self.last_active = now

    def update(self, now) -> None:
        if now - self.last_active > config.HAND_RETURN_MS / 1000.0:
            self.tx, self.ty = float(self.rest[0]), float(self.rest[1])
        self.x += (self.tx - self.x) * config.HAND_EASE
        self.y += (self.ty - self.y) * config.HAND_EASE
        self.tap *= config.HAND_DECAY_PER_FRAME
        if self.tap < 0.02:
            self.tap = 0.0

    def is_animating(self) -> bool:
        """True while the glove is still moving toward its target or tapping."""
        return (abs(self.tx - self.x) > 0.5 or abs(self.ty - self.y) > 0.5
                or self.tap > 0.0)


class Hands:
    def __init__(self, glove_pixmap, hand_layout=None) -> None:
        self.glove = glove_pixmap
        self._hand_layout = hand_layout or {
            "tip": (config.HAND_TIP_FX, config.HAND_TIP_FY),
            "wrist": (config.HAND_WRIST_FX, config.HAND_WRIST_FY),
        }
        self._gw = glove_pixmap.width() * config.HAND_SCALE
        self._gh = glove_pixmap.height() * config.HAND_SCALE
        self._glove_scaled = glove_pixmap        # replaced by prepare()
        self._dpr = 1.0
        self.left = _Hand(config.LEFT_REST, config.LEFT_SHOULDER)
        self.right = _Hand(config.RIGHT_REST, config.RIGHT_SHOULDER)

    def prepare(self, dpr: float) -> None:
        """Pre-scale the glove to its device-pixel size once (issue #2)."""
        self._dpr = dpr or 1.0
        self._glove_scaled = scale_for_display(self.glove, self._gw, self._gh, self._dpr)

    def set_glove(self, glove_pixmap, hand_layout=None) -> None:
        """Swap the glove art (issue #5: skins). The scaled copy is rebuilt by
        the next prepare()."""
        self.glove = glove_pixmap
        if hand_layout is not None:
            self._hand_layout = hand_layout
        self._gw = glove_pixmap.width() * config.HAND_SCALE
        self._gh = glove_pixmap.height() * config.HAND_SCALE
        self._glove_scaled = glove_pixmap
        self._dpr = 1.0

    def press_key(self, side: str, target, now) -> None:
        (self.left if side == "left" else self.right).activate(target, now)

    def track(self, side: str, target, now) -> None:
        (self.left if side == "left" else self.right).track(target, now)

    def update(self, now) -> None:
        self.left.update(now)
        self.right.update(now)

    def is_animating(self) -> bool:
        return self.left.is_animating() or self.right.is_animating()

    def hand_tip_fraction(self) -> tuple[float, float]:
        return self._hand_layout["tip"]

    # ---- drawing ----
    def draw(self, painter, lean_x: float = 0.0, body_y: float = 0.0) -> None:
        self.draw_sleeves(painter, lean_x, body_y)
        self.draw_gloves(painter)

    def draw_sleeves(self, painter, lean_x: float = 0.0, body_y: float = 0.0) -> None:
        self._draw_sleeve_for_one(painter, self.right, lean_x, body_y)
        self._draw_sleeve_for_one(painter, self.left, lean_x, body_y)

    def draw_gloves(self, painter) -> None:
        self._draw_glove_for_one(painter, self.right, True)
        self._draw_glove_for_one(painter, self.left, False)

    def _draw_sleeve_for_one(self, p, hand, lean_x, body_y) -> None:
        x, y, gw, gh = self._glove_rect(hand)
        shoulder = (hand.shoulder[0] + lean_x, hand.shoulder[1] + body_y)
        wrist_fx, wrist_fy = self._hand_layout["wrist"]
        wrist = (x + wrist_fx * gw, y + wrist_fy * gh)
        self._draw_sleeve(p, shoulder, wrist)

    def _draw_glove_for_one(self, p, hand, mirror) -> None:
        x, y, gw, gh = self._glove_rect(hand)
        pm = self._glove_scaled
        src = QRectF(0, 0, pm.width(), pm.height())
        if mirror:
            p.save()
            p.translate(x + gw, y)
            p.scale(-1, 1)
            p.drawPixmap(QRectF(0, 0, gw, gh), pm, src)
            p.restore()
        else:
            p.drawPixmap(QRectF(x, y, gw, gh), pm, src)

    def _glove_rect(self, hand):
        tip_x = hand.x
        tip_y = hand.y + config.HAND_TAP_DIP * hand.tap
        gw, gh = self._gw, self._gh
        tip_fx, tip_fy = self._hand_layout["tip"]
        x = tip_x - tip_fx * gw
        y = tip_y - tip_fy * gh
        # Snap the glove origin to the device-pixel grid (issue #2).
        dpr = self._dpr
        x = round(x * dpr) / dpr
        y = round(y * dpr) / dpr
        return x, y, gw, gh

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
