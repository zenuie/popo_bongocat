"""A small settings panel opened from the tray (issue #5).

Hosts the user-facing controls for the three configurable behaviours: global
scale (#4), active skin (#5) and the mouse-follow toggle (#3). Every control
applies live to the running window and persists via src.settings.
"""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QSizePolicy, QSlider, QVBoxLayout, QWidget,
)
from PySide6.QtWidgets import QDialog

from . import config, settings, skins


class SettingsDialog(QDialog):
    def __init__(self, window, parent=None) -> None:
        super().__init__(parent)
        self._window = window
        self.setWindowTitle("Po 設定")
        self.setMinimumWidth(320)

        form = QFormLayout()

        # --- size (issue #4) ---
        self._scale = QSlider(Qt.Horizontal)
        self._scale.setRange(int(settings.SCALE_MIN * 100), int(settings.SCALE_MAX * 100))
        self._scale.setSingleStep(5)
        self._scale.setPageStep(25)
        self._scale.setValue(int(round(config.PET_SCALE * 100)))
        self._scale_value = QLabel()
        self._scale.valueChanged.connect(self._on_scale)
        size_row = QHBoxLayout()
        size_row.addWidget(self._scale, 1)
        size_row.addWidget(self._scale_value)
        form.addRow("尺寸", _row_widget(size_row))
        self._refresh_scale_label()

        # --- skin (issue #5) ---
        self._skin = QComboBox()
        self._reload_skins()
        self._skin.currentTextChanged.connect(self._on_skin)
        form.addRow("造型", self._skin)

        self._align_hand = QPushButton("調整...")
        self._align_hand.clicked.connect(self._on_align_hand)
        form.addRow("手部對齊", self._align_hand)

        # --- mouse follow (issue #3) ---
        self._follow = QCheckBox("讓 Po 的手跟著滑鼠移動")
        self._follow.setChecked(config.FOLLOW_MOUSE)
        self._follow.toggled.connect(self._on_follow)
        form.addRow("滑鼠", self._follow)

        hint = QLabel(
            "自訂造型：在設定資料夾的 skins/<名稱>/ 放入 "
            "po_body.png 與 po_hand.png。詳見 docs/skins.md。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 11px;")

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)

    # ---- handlers -----------------------------------------------------
    def _on_scale(self, percent: int) -> None:
        self._window.set_scale(percent / 100.0)
        self._refresh_scale_label()

    def _refresh_scale_label(self) -> None:
        self._scale_value.setText(f"{self._scale.value()}%")

    def _on_skin(self, name: str) -> None:
        if name:
            self._window.set_skin(name)

    def _on_follow(self, checked: bool) -> None:
        config.FOLLOW_MOUSE = checked
        settings.save(follow_mouse=checked)

    def _on_align_hand(self) -> None:
        name = self._skin.currentText()
        if not skins.writable_skin_meta_path(name):
            QMessageBox.information(
                self,
                "手部對齊",
                "目前只支援儲存到使用者自訂造型。請把造型放在設定資料夾的 skins/<名稱>/。",
            )
            return
        assets = skins.skin_assets(name)
        if assets is None:
            return
        dialog = HandAlignmentDialog(name, assets[1], skins.skin_hand_layout(name), self)
        if dialog.exec() != QDialog.Accepted:
            return
        if not skins.save_skin_hand_layout(name, dialog.hand_layout()):
            QMessageBox.warning(self, "手部對齊", "無法儲存手部對齊設定。")
            return
        self._window.set_skin(name)

    def _reload_skins(self) -> None:
        self._skin.blockSignals(True)
        self._skin.clear()
        self._skin.addItems(skins.available_skins())
        current = config.ACTIVE_SKIN if config.ACTIVE_SKIN in skins.available_skins() else skins.DEFAULT
        self._skin.setCurrentText(current)
        self._skin.blockSignals(False)

    def showEvent(self, event) -> None:
        # re-scan for newly dropped-in skins each time the panel opens
        self._reload_skins()
        super().showEvent(event)


def _row_widget(layout) -> QWidget:
    w = QWidget()
    layout.setContentsMargins(0, 0, 0, 0)
    w.setLayout(layout)
    return w


class HandAlignmentDialog(QDialog):
    def __init__(self, skin_name: str, hand_path: str, hand_layout, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"手部對齊 - {skin_name}")
        self.setMinimumWidth(360)

        pixmap = QPixmap(hand_path)
        self._editor = _HandAnchorEditor(pixmap, hand_layout)

        hint = QLabel("拖曳按壓點與袖口點，調整手套和袖子的接合位置。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 11px;")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel | QDialogButtonBox.Reset)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Reset).clicked.connect(self._editor.reset_to_default)

        layout = QVBoxLayout(self)
        layout.addWidget(self._editor)
        layout.addWidget(hint)
        layout.addWidget(buttons)

    def hand_layout(self) -> dict[str, tuple[float, float]]:
        return self._editor.hand_layout()


class _HandAnchorEditor(QWidget):
    _POINT_RADIUS = 8.0

    def __init__(self, pixmap: QPixmap, hand_layout, parent=None) -> None:
        super().__init__(parent)
        self._pixmap = pixmap
        self._points = {
            "tip": QPointF(*hand_layout["tip"]),
            "wrist": QPointF(*hand_layout["wrist"]),
        }
        self._active = None
        self.setMinimumSize(320, 280)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def reset_to_default(self) -> None:
        layout = skins.default_hand_layout()
        self._points = {
            "tip": QPointF(*layout["tip"]),
            "wrist": QPointF(*layout["wrist"]),
        }
        self.update()

    def hand_layout(self) -> dict[str, tuple[float, float]]:
        return {
            name: (point.x(), point.y())
            for name, point in self._points.items()
        }

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor("#202124"))
        image_rect = self._image_rect()
        if not self._pixmap.isNull():
            p.drawPixmap(image_rect, self._pixmap, QRectF(0, 0, self._pixmap.width(), self._pixmap.height()))

        p.setPen(QPen(QColor("#ffffff"), 1))
        p.drawRect(image_rect)
        self._draw_point(p, "wrist", QColor("#45B7D1"), "袖口")
        self._draw_point(p, "tip", QColor("#F2742F"), "按壓")

    def mousePressEvent(self, event) -> None:
        self._active = self._nearest_point(event.position())
        self._move_active(event.position())

    def mouseMoveEvent(self, event) -> None:
        if self._active is not None:
            self._move_active(event.position())

    def mouseReleaseEvent(self, _event) -> None:
        self._active = None

    def _draw_point(self, painter, name: str, color: QColor, label: str) -> None:
        pos = self._point_to_widget(self._points[name])
        painter.setPen(QPen(QColor("#111111"), 2))
        painter.setBrush(color)
        painter.drawEllipse(pos, self._POINT_RADIUS, self._POINT_RADIUS)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawText(pos + QPointF(12, -10), label)

    def _nearest_point(self, pos: QPointF):
        distances = {
            name: (self._point_to_widget(point) - pos).manhattanLength()
            for name, point in self._points.items()
        }
        name = min(distances, key=distances.get)
        return name if distances[name] <= 24 else None

    def _move_active(self, pos: QPointF) -> None:
        if self._active is None:
            return
        rect = self._image_rect()
        x = (pos.x() - rect.x()) / rect.width() if rect.width() else 0.0
        y = (pos.y() - rect.y()) / rect.height() if rect.height() else 0.0
        self._points[self._active] = QPointF(_clamp01(x), _clamp01(y))
        self.update()

    def _point_to_widget(self, point: QPointF) -> QPointF:
        rect = self._image_rect()
        return QPointF(rect.x() + point.x() * rect.width(), rect.y() + point.y() * rect.height())

    def _image_rect(self) -> QRectF:
        margin = 18.0
        bounds = QRectF(margin, margin, self.width() - margin * 2, self.height() - margin * 2)
        if self._pixmap.isNull():
            return bounds
        scale = min(bounds.width() / self._pixmap.width(), bounds.height() / self._pixmap.height())
        w = self._pixmap.width() * scale
        h = self._pixmap.height() * scale
        return QRectF(bounds.center().x() - w / 2, bounds.center().y() - h / 2, w, h)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
