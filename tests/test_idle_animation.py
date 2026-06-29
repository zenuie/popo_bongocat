"""Tests for the idle-repaint gate (issue #1: high idle CPU).

The fix stops repainting/re-masking every frame. The per-frame loop must only
trigger a repaint when something is actually animating. These tests cover the
pure predicates that decide that — no QApplication / display required.
"""
from src import config
from src.hands import _Hand
from src.keyboard import KeyboardGraphic
from src.mouse import MouseGraphic


def _settle(component, steps: int = 2000) -> None:
    for _ in range(steps):
        component.update()


# ---- keyboard -------------------------------------------------------------
def test_keyboard_is_idle_on_construction():
    assert KeyboardGraphic().is_animating() is False


def test_keyboard_animates_after_press():
    kb = KeyboardGraphic()
    kb.press("a")
    assert kb.is_animating() is True


def test_keyboard_settles_back_to_idle():
    kb = KeyboardGraphic()
    kb.press("a")
    _settle(kb)
    assert kb.is_animating() is False


# ---- mouse ----------------------------------------------------------------
def test_mouse_is_idle_on_construction():
    assert MouseGraphic().is_animating() is False


def test_mouse_animates_after_click_and_scroll():
    ms = MouseGraphic()
    ms.press("left")
    assert ms.is_animating() is True
    ms2 = MouseGraphic()
    ms2.scroll()
    assert ms2.is_animating() is True


def test_mouse_settles_back_to_idle():
    ms = MouseGraphic()
    ms.press("right")
    _settle(ms)
    assert ms.is_animating() is False


# ---- a single hand --------------------------------------------------------
def test_hand_at_rest_is_idle():
    hand = _Hand(config.LEFT_REST, config.LEFT_SHOULDER)
    assert hand.is_animating() is False


def test_hand_animates_right_after_activation():
    hand = _Hand(config.LEFT_REST, config.LEFT_SHOULDER)
    hand.activate((100.0, 170.0), now=1000.0)
    assert hand.is_animating() is True


def test_hand_returns_to_rest_and_settles():
    hand = _Hand(config.LEFT_REST, config.LEFT_SHOULDER)
    hand.activate((100.0, 170.0), now=1000.0)
    # advance time well past HAND_RETURN_MS so it eases back to rest
    for i in range(2000):
        hand.update(now=1000.0 + i * 0.05)
    assert hand.is_animating() is False


# ---- mouse-follow tracking (issue #3) -------------------------------------
def test_track_does_not_press_down():
    hand = _Hand(config.LEFT_REST, config.LEFT_SHOULDER)
    hand.track((52.0, 198.0), now=1000.0)
    assert hand.tap == 0.0            # resting on the mouse, not tapping it
    assert hand.is_animating() is True


def test_tracked_hand_returns_to_rest_when_cursor_goes_still():
    hand = _Hand(config.LEFT_REST, config.LEFT_SHOULDER)
    hand.track((52.0, 198.0), now=1000.0)
    for i in range(2000):            # stop tracking; time marches on
        hand.update(now=1000.0 + i * 0.05)
    assert abs(hand.x - config.LEFT_REST[0]) < 1.0
    assert abs(hand.y - config.LEFT_REST[1]) < 1.0
    assert hand.is_animating() is False
