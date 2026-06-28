"""Po body motion: a gentle idle float plus a small downward nod on activity.
One QTimer drives it; the window reads `offset_y` each frame.
"""
import math

from PySide6.QtCore import QElapsedTimer, QObject, QTimer, Signal

from . import config


class Animator(QObject):
    frame = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(config.FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)
        self._clock = QElapsedTimer()
        self._nod = 0.0
        self.offset_y = 0.0

    def start(self) -> None:
        self._clock.start()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def nod(self) -> None:
        self._nod = config.NOD_DIP

    def _tick(self) -> None:
        t = self._clock.elapsed() / 1000.0
        float_y = config.FLOAT_AMPLITUDE * math.sin(2 * math.pi * t / config.FLOAT_PERIOD)
        self._nod *= config.HAND_DECAY_PER_FRAME
        if self._nod < 0.05:
            self._nod = 0.0
        self.offset_y = float_y + self._nod
        self.frame.emit()
