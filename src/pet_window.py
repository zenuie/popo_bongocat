"""Po's window: transparent, always-on-top, draggable, click-through.

Scene (back to front): Po's body (floats) -> the desk (rotated keyboard +
mouse, fixed) -> Po's hands (program-controlled, reach the pressed key/mouse).
Global key/mouse input drives which hand reaches where and lights the key.
"""
import time
from typing import Optional

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBitmap, QGuiApplication, QPainter, QPixmap, QRegion, QTransform
from PySide6.QtWidgets import QWidget

from . import config, settings
from .animator import Animator
from .desk import Desk
from .hands import Hands
from .resources import resource_path
from .sprites import scale_for_display


class PetWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._body = QPixmap(resource_path(config.asset_path("parts/po_body.png")))
        glove = QPixmap(resource_path(config.asset_path("parts/po_hand.png")))

        self._setup_window()

        self._animator = Animator(self)
        self._animator.frame.connect(self._on_frame)
        self._desk = Desk()
        self._hands = Hands(glove)

        # Mask the click/hit region ONCE to the area Po can ever occupy, instead
        # of rebuilding + re-applying it every frame (issue #1: idle CPU).
        self._apply_mask()
        self._last_paint_pos: Optional[tuple[int, int]] = None

        # Pre-scaled sprites (issue #2). Rebuilt whenever the render factor
        # (PET_SCALE x device pixel ratio) changes — a new monitor or a live
        # scale change (issue #4).
        self._sprite_factor = 0.0
        self._body_scaled = self._body

        # body lean (toward the active hand's target)
        self._lean = 0.0
        self._lean_target = 0.0
        self._lean_last = -1e9

        # drag state
        self._dragging = False
        self._dragged = False
        self._press_global = None
        self._press_window = None
        self._last_nod = 0.0

        self.move_to_default_corner()
        self._animator.start()

    # ---- setup --------------------------------------------------------
    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        always_show = getattr(Qt, "WA_MacAlwaysShowToolWindow", None)
        if always_show is not None:
            self.setAttribute(always_show, True)
        self._resize_to_scale()

    def _resize_to_scale(self) -> None:
        self.setFixedSize(round(config.CANVAS_WIDTH * config.PET_SCALE),
                          round(config.CANVAS_HEIGHT * config.PET_SCALE))

    def move_to_default_corner(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        margin = 24
        self.move(geo.right() - self.width() - margin,
                  geo.bottom() - self.height() - margin)

    # ---- rendering ----------------------------------------------------
    def _body_size(self):
        return self._body.width() * config.PO_BODY_SCALE, self._body.height() * config.PO_BODY_SCALE

    def _build_body_mask(self) -> QRegion:
        bw, bh = (int(round(v)) for v in self._body_size())
        scaled = self._body.scaled(bw, bh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        region = QRegion(QBitmap.fromImage(scaled.toImage().createAlphaMask()))
        region.translate(int(round(config.PO_CENTER_X - bw / 2)), config.PO_BODY_TOP)
        return region

    def _build_static_mask(self) -> QRegion:
        """A single mask covering every position the body can occupy — it leans
        +/-BODY_LEAN_MAX horizontally and floats/nods vertically — unioned with
        the fixed desk. Recomputing this mask each frame was the dominant idle
        cost, so we sweep the range once here and never call setMask again."""
        body = self._build_body_mask()
        swept = QRegion()
        x_max = config.BODY_LEAN_MAX
        y_lo = -int(config.FLOAT_AMPLITUDE) - 1
        y_hi = int(config.FLOAT_AMPLITUDE + config.NOD_DIP) + 1
        for dx in range(-x_max, x_max + 1, 10):
            for dy in (y_lo, 0, y_hi):
                swept = swept.united(body.translated(dx, dy))
        return swept.united(self._desk.mask_region())

    def _apply_mask(self) -> None:
        """Set the click/hit mask, scaled from base coords into window coords."""
        s = config.PET_SCALE
        self.setMask(QTransform().scale(s, s).map(self._build_static_mask()))

    def _render_factor(self) -> float:
        """Base-coord -> physical-pixel factor: global scale x device pixel ratio."""
        return config.PET_SCALE * self.devicePixelRatioF()

    def _ensure_sprites(self) -> None:
        """(Re)build device-resolution sprites when the render factor changes."""
        factor = self._render_factor()
        if factor == self._sprite_factor:
            return
        self._sprite_factor = factor
        bw, bh = self._body_size()
        self._body_scaled = scale_for_display(self._body, bw, bh, factor)
        self._hands.prepare(factor)

    def paintEvent(self, _event) -> None:
        self._ensure_sprites()
        factor = self._sprite_factor or 1.0

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        # One transform scales the whole base-coord scene (issue #4); all
        # drawing below stays in authored 1.0 coordinates.
        p.scale(config.PET_SCALE, config.PET_SCALE)

        bw, bh = self._body_size()
        bx = config.PO_CENTER_X + self._lean - bw / 2
        by = config.PO_BODY_TOP + self._animator.offset_y
        # Snap to the physical-pixel grid so a 1:1 blit stays crisp and edges
        # don't crawl as Po breathes through sub-pixel offsets (issue #2).
        bx = round(bx * factor) / factor
        by = round(by * factor) / factor
        p.drawPixmap(QRectF(bx, by, bw, bh), self._body_scaled,
                     QRectF(0, 0, self._body_scaled.width(), self._body_scaled.height()))

        self._desk.draw(p)
        self._hands.draw(p, self._lean)

    # ---- live scale (issue #4) ----------------------------------------
    def set_scale(self, scale: float) -> None:
        scale = min(settings.SCALE_MAX, max(settings.SCALE_MIN, float(scale)))
        if abs(scale - config.PET_SCALE) < 1e-3:
            return
        config.PET_SCALE = scale
        self._resize_to_scale()
        self._apply_mask()
        self._sprite_factor = 0.0          # force a rebuild at the new factor
        self.move_to_default_corner()
        self.update()
        settings.save(scale=scale)

    def _on_frame(self) -> None:
        now = time.monotonic()
        self._hands.update(now)
        self._desk.update()
        if now - self._lean_last > config.HAND_RETURN_MS / 1000.0:
            self._lean_target = 0.0
        self._lean += (self._lean_target - self._lean) * config.BODY_LEAN_EASE
        if self._needs_repaint():
            self.update()

    def _needs_repaint(self) -> bool:
        """Repaint only when the rendered scene would actually differ. An idle
        Po only breathes, so its rounded position changes a few times a second
        rather than 60 — the rest of the frames are skipped (issue #1)."""
        pos = (round(config.PO_CENTER_X + self._lean),
               round(config.PO_BODY_TOP + self._animator.offset_y))
        if pos != self._last_paint_pos:
            self._last_paint_pos = pos
            return True
        return self._hands.is_animating() or self._desk.is_animating()

    # ---- global activity (Bongo Cat) ---------------------------------
    def _lean_to(self, target_x: float, now: float) -> None:
        raw = (target_x - config.PO_CENTER_X) * config.BODY_LEAN_FACTOR
        self._lean_target = max(-config.BODY_LEAN_MAX, min(config.BODY_LEAN_MAX, raw))
        self._lean_last = now

    def on_key(self, token: str) -> None:
        if self._dragging:
            return
        target = self._desk.key_target(token)
        self._desk.press_key(token)
        now = time.monotonic()
        if target:
            wx, wy, side = target
            self._hands.press_key(side, (wx, wy), now)
            self._lean_to(wx, now)
        if now - self._last_nod >= config.REACTION_THROTTLE_S:
            self._last_nod = now
            self._animator.nod()

    def on_mouse_button(self, button: str) -> None:
        if self._dragging:
            return
        mx, my, side = self._desk.mouse_target()
        now = time.monotonic()
        self._desk.press_mouse(button)
        self._hands.press_key(side, (mx, my), now)
        self._lean_to(mx, now)

    def on_scroll(self) -> None:
        if self._dragging:
            return
        mx, my, side = self._desk.mouse_target()
        now = time.monotonic()
        self._desk.scroll()
        self._hands.press_key(side, (mx, my), now)
        self._lean_to(mx, now)

    # ---- dragging -----------------------------------------------------
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._press_global = event.globalPosition().toPoint()
            self._press_window = self.pos()
            self._dragging = False
            self._dragged = False
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._press_global is None:
            return
        delta = event.globalPosition().toPoint() - self._press_global
        if not self._dragging and delta.manhattanLength() > config.DRAG_THRESHOLD:
            self._dragging = True
            self._dragged = True
        if self._dragging:
            self.move(self._press_window + delta)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        self._press_global = None
        self._press_window = None
        self._dragging = False
        self._dragged = False
        event.accept()
