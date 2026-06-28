"""Resolve bundled asset paths in both dev and PyInstaller builds."""
import os
import sys


def resource_path(relative: str) -> str:
    """Return an absolute path to `relative`, resolved against the PyInstaller
    bundle dir when frozen, otherwise the project root (one level above src/).
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)
