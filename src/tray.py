"""System-tray icon + menu: open settings, reset position, quit."""
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import config
from .resources import resource_path
from .settings_dialog import SettingsDialog


def _open_settings(window) -> None:
    dialog = getattr(window, "_settings_dialog", None)
    if dialog is None:
        dialog = SettingsDialog(window)
        window._settings_dialog = dialog       # keep it alive
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()


def build_tray(app: QApplication, window) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(QIcon(resource_path(config.asset_path("idle.png"))), app)
    tray.setToolTip("Po 桌寵")

    menu = QMenu()
    settings_action = menu.addAction("設定…")
    settings_action.triggered.connect(lambda: _open_settings(window))
    menu.addSeparator()
    reset = menu.addAction("重置位置")
    reset.triggered.connect(window.move_to_default_corner)
    menu.addSeparator()
    quit_action = menu.addAction("結束")
    quit_action.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.show()
    return tray
