"""Pure mapping from a global cursor position to Po's small desk-mouse offset.

The real cursor roams the whole screen; Po's little mouse should echo that as a
gentle, scaled-down wiggle (not 1:1) so it reads as "Po is nudging the mouse".
Kept pure (no Qt) so it's trivially testable.
"""


def pointer_to_offset(px: float, py: float,
                      screen_x: float, screen_y: float,
                      screen_w: float, screen_h: float,
                      range_x: float, range_y: float) -> tuple[float, float]:
    """Map an absolute cursor (px, py) to a (dx, dy) offset in [-range, +range].

    The cursor's position within the screen is normalised to 0..1, clamped (so
    a cursor on another monitor rests at the edge), then centred and scaled.
    """
    if screen_w <= 0 or screen_h <= 0:
        return (0.0, 0.0)
    nx = min(1.0, max(0.0, (px - screen_x) / screen_w))
    ny = min(1.0, max(0.0, (py - screen_y) / screen_h))
    return ((nx - 0.5) * 2.0 * range_x, (ny - 0.5) * 2.0 * range_y)
