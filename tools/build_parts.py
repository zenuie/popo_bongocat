"""Regenerate Po's body + hand sprites from the source art.

Reads  assets/parts/source_po_idle.png  (the full-res Po sticker) and writes:
  assets/parts/po_body.png  - head + torso, arms removed, clean rounded bottom
  assets/parts/po_hand.png  - one clean white glove (white fill + black outline,
                              no white sticker halo); mirrored in code for the
                              other hand.

Run from the project root:  python tools/build_parts.py
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "parts")
SRC = os.path.join(OUT, "source_po_idle.png")
os.makedirs(OUT, exist_ok=True)

# Ellipse modelling Po's lower torso (in the de-backgrounded idle's coords),
# used to cut the arms off and round the body's bottom.
BODY_CX, BODY_CAP_TOP, BODY_RX, BODY_RY = 257, 380, 210, 132


def debg(path):
    """Remove the cream background via edge-connectivity (stopped by Po's white
    sticker outline), keep the largest blob, trim a 1px fringe, crop to content."""
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3].astype(np.int16)
    corners = np.array([arr[2, 2, :3], arr[2, w - 3, :3],
                        arr[h - 3, 2, :3], arr[h - 3, w - 3, :3]], dtype=np.int16)
    bg = np.median(corners, axis=0)
    bg_like = np.sqrt(((rgb - bg) ** 2).sum(axis=2)) < 42
    lbl, _ = ndimage.label(bg_like)
    border = set(lbl[0, :]) | set(lbl[-1, :]) | set(lbl[:, 0]) | set(lbl[:, -1])
    border.discard(0)
    opaque = ~np.isin(lbl, list(border))
    lbl2, n2 = ndimage.label(opaque)
    sizes = ndimage.sum(np.ones_like(lbl2), lbl2, range(1, n2 + 1))
    opaque = lbl2 == int(np.argmax(sizes)) + 1
    opaque = ndimage.binary_erosion(opaque, iterations=1)
    out = arr.copy()
    out[:, :, 3] = np.where(opaque, 255, 0).astype(np.uint8)
    ys, xs = np.where(opaque)
    return out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def build_body(idle):
    h, w = idle.shape[:2]
    alpha = idle[:, :, 3]
    yy, xx = np.mgrid[0:h, 0:w]
    inside = ((xx - BODY_CX) / BODY_RX) ** 2 + ((yy - BODY_CAP_TOP) / BODY_RY) ** 2 <= 1.0
    new_a = alpha.copy()
    below = yy >= BODY_CAP_TOP
    new_a[below & ~(inside & below)] = 0
    op = new_a > 20
    lbl, n = ndimage.label(op)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
        new_a[lbl != int(np.argmax(sizes)) + 1] = 0
    out = idle.copy()
    out[:, :, 3] = new_a
    ys, xs = np.where(new_a > 20)
    Image.fromarray(out[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA").save(
        os.path.join(OUT, "po_body.png"))


def build_hand(idle):
    h, w = idle.shape[:2]
    rgb = idle[:, :, :3].astype(int)
    a = idle[:, :, 3]
    white = (rgb.min(axis=2) > 240) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 10) & (a > 128)
    lower = np.zeros((h, w), bool)
    lower[int(h * 0.55):, :] = True
    lbl, n = ndimage.label(white & lower)
    gloves = []
    for i in range(1, n + 1):
        ys, xs = np.where(lbl == i)
        if len(xs) < 3000 or (xs.max() - xs.min()) > 200 or (ys.max() - ys.min()) > 200:
            continue
        gloves.append((xs.min(), xs.max(), ys.min(), ys.max(), (xs.min() + xs.max()) // 2))
    gx0, gx1, gy0, gy1, _ = min(gloves, key=lambda c: c[4])  # leftmost glove
    pad = 16
    bx0, by0 = max(0, gx0 - pad), max(0, gy0 - pad)
    bx1, by1 = min(w, gx1 + pad), min(h, gy1 + pad)

    sub = idle[by0:by1, bx0:bx1, :].copy()
    srgb = sub[:, :, :3].astype(int)
    sa = sub[:, :, 3]
    opaque = sa > 100
    fill_white = opaque & (srgb.min(axis=2) > 225) & ((srgb.max(axis=2) - srgb.min(axis=2)) < 18)
    dark = opaque & (srgb.max(axis=2) < 140)
    lblw, nw = ndimage.label(fill_white)
    szw = ndimage.sum(np.ones_like(lblw), lblw, range(1, nw + 1))
    fill = lblw == int(np.argmax(szw)) + 1
    keep = fill | (ndimage.binary_dilation(fill, iterations=5) & dark)
    lblk, nk = ndimage.label(keep)
    if nk > 1:
        szk = ndimage.sum(np.ones_like(lblk), lblk, range(1, nk + 1))
        keep = lblk == int(np.argmax(szk)) + 1
    keep = ndimage.binary_fill_holes(keep)
    out = sub.copy()
    out[:, :, 3] = np.where(keep, 255, 0).astype(np.uint8)
    ys, xs = np.where(keep)
    Image.fromarray(out[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA").save(
        os.path.join(OUT, "po_hand.png"))


def main():
    idle = debg(SRC)
    build_body(idle)
    build_hand(idle)
    print("wrote", os.path.join(OUT, "po_body.png"), "and po_hand.png")


if __name__ == "__main__":
    main()
