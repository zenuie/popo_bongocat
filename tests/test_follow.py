"""Tests for the cursor -> desk-mouse offset mapping (issue #3)."""
import pytest

from src import config
from src.follow import pointer_to_offset

SCREEN = (0, 0, 1000, 800)   # x, y, w, h
RANGE = (20.0, 10.0)


def _map(px, py):
    return pointer_to_offset(px, py, *SCREEN, *RANGE)


def test_center_maps_to_zero_offset():
    assert _map(500, 400) == (0.0, 0.0)


def test_corners_map_to_full_range():
    assert _map(1000, 800) == (20.0, 10.0)
    assert _map(0, 0) == (-20.0, -10.0)


def test_offscreen_cursor_is_clamped_to_edge():
    assert _map(5000, 4000) == (20.0, 10.0)
    assert _map(-999, -999) == (-20.0, -10.0)


def test_offset_scales_down_not_one_to_one():
    dx, _ = _map(750, 400)   # 75% across a 1000px screen
    assert dx == 10.0        # quarter of the way -> +half range, far below 250px


def test_zero_sized_screen_is_safe():
    assert pointer_to_offset(100, 100, 0, 0, 0, 0, 20, 10) == (0.0, 0.0)


# ---- desk-mouse offset easing (needs a QGuiApplication for QRegion) --------
@pytest.fixture(scope="module")
def _app():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app


def test_desk_mouse_offset_eases_toward_target_and_settles(_app):
    from src.desk import Desk
    desk = Desk()
    desk.set_mouse_offset_target(config.MOUSE_FOLLOW_RANGE_X, config.MOUSE_FOLLOW_RANGE_Y)
    assert desk.is_animating() is True
    for _ in range(500):
        desk.update()
    ox, oy = desk._mouse_offset
    assert abs(ox - config.MOUSE_FOLLOW_RANGE_X) < 0.5
    assert abs(oy - config.MOUSE_FOLLOW_RANGE_Y) < 0.5
    assert desk.is_animating() is False


def test_mouse_target_includes_offset(_app):
    from src.desk import Desk
    desk = Desk()
    base_cx = config.MOUSE_RECT[0] + config.MOUSE_RECT[2] * 0.5
    desk.set_mouse_offset_target(10.0, 4.0)
    for _ in range(500):
        desk.update()
    mx, _my, _side = desk.mouse_target()
    assert abs(mx - (base_cx + 10.0)) < 0.5

