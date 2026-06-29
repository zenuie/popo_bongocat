"""Pre-scale sprite pixmaps to their on-screen device size, once.

Drawing a ~3.2x-downscaled pixmap on the fly every frame — at the sub-pixel,
breathing offsets Po floats through — produced moiré on fine detail and edge
shimmer between frames (issue #2). Two things cause that:

  * a big one-shot bilinear downscale under-filters high-frequency detail, and
  * resampling at a different sub-pixel phase each frame makes edges crawl.

So we scale each sprite to its exact device-pixel target a single time, with a
multi-step reduction (halving until close) that filters cleanly, then the
window blits it 1:1 at a device-pixel-snapped position.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


def scale_for_display(src: QPixmap, w: float, h: float, dpr: float) -> QPixmap:
    """Return `src` scaled to ``w x h`` *logical* px rendered at device
    resolution (``round(w*dpr) x round(h*dpr)`` actual pixels).

    The reduction is done in <=2x steps so a large downscale doesn't alias the
    way a single bilinear pass would.
    """
    target_w = max(1, round(w * dpr))
    target_h = max(1, round(h * dpr))

    out = src
    # Halve repeatedly while still well above the target — each halving is a
    # clean 2x box-ish reduction, avoiding the moiré of one big jump.
    while out.width() > target_w * 2 and out.height() > target_h * 2:
        out = out.scaled(out.width() // 2, out.height() // 2,
                         Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    if out.width() != target_w or out.height() != target_h:
        out = out.scaled(target_w, target_h,
                         Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    return out
