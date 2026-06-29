"""Tests for sprite pre-scaling (issue #2: moiré / shimmer).

`scale_for_display` must produce a pixmap at the exact device-pixel target so
it can be blitted 1:1 instead of downscaled on the fly every frame.
"""
import pytest
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication

from src.sprites import scale_for_display


@pytest.fixture(scope="module", autouse=True)
def _app():
    app = QApplication.instance() or QApplication([])
    yield app


def _src(w: int, h: int) -> QPixmap:
    pm = QPixmap(w, h)
    pm.fill(QColor("white"))
    return pm


def test_scales_to_device_pixels_at_dpr_1():
    out = scale_for_display(_src(518, 513), 161, 159, dpr=1.0)
    assert (out.width(), out.height()) == (161, 159)


def test_scales_to_device_pixels_at_dpr_2():
    out = scale_for_display(_src(518, 513), 161, 159, dpr=2.0)
    assert (out.width(), out.height()) == (322, 318)


def test_actually_downscales_a_large_source():
    out = scale_for_display(_src(518, 513), 40, 41, dpr=1.0)
    assert out.width() < 518 and out.height() < 513


def test_never_returns_zero_sized_pixmap():
    out = scale_for_display(_src(130, 132), 0.4, 0.4, dpr=1.0)
    assert out.width() >= 1 and out.height() >= 1
