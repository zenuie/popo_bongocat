"""System-tray icon + menu: size presets, reset position, quit."""
from PySide6.QtGui import QActionGroup, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import config
from .resources import resource_path

SCALE_PRESETS = [("75%", 0.75), ("100%", 1.0), ("125%", 1.25), ("150%", 1.5)]


def _add_scale_menu(menu: QMenu, window) -> None:
    sub = menu.addMenu("尺寸")
    group = QActionGroup(sub)
    group.setExclusive(True)
    for label, value in SCALE_PRESETS:
        action = sub.addAction(label)
        action.setCheckable(True)
        action.setChecked(abs(config.PET_SCALE - value) < 1e-3)
        group.addAction(action)
        action.triggered.connect(lambda _checked=False, v=value: window.set_scale(v))


def build_tray(app: QApplication, window) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(QIcon(resource_path(config.asset_path("idle.png"))), app)
    tray.setToolTip("Po 桌寵")

    menu = QMenu()
    _add_scale_menu(menu, window)
    menu.addSeparator()
    reset = menu.addAction("重置位置")
    reset.triggered.connect(window.move_to_default_corner)
    menu.addSeparator()
    quit_action = menu.addAction("結束")
    quit_action.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.show()
    return tray
