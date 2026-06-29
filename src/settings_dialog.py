"""A small settings panel opened from the tray (issue #5).

Hosts the user-facing controls for the three configurable behaviours: global
scale (#4), active skin (#5) and the mouse-follow toggle (#3). Every control
applies live to the running window and persists via src.settings.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QSlider, QVBoxLayout, QWidget,
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
