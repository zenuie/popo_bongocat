"""Tests for skin discovery / resolution (issue #5)."""
import os

import pytest

from src import settings, skins


@pytest.fixture
def skins_root(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "config_dir", lambda: str(tmp_path))
    # point bundled dir somewhere empty so only user skins show up
    monkeypatch.setattr(skins, "_bundled_skins_dir", lambda: str(tmp_path / "bundled"))
    return tmp_path / "skins"


def _make_skin(root, name, body=True, hand=True):
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    if body:
        (folder / skins.BODY_FILE).write_bytes(b"x")
    if hand:
        (folder / skins.HAND_FILE).write_bytes(b"x")
    return folder


def test_default_always_available(skins_root):
    assert skins.available_skins() == ["default"]


def test_valid_user_skins_are_listed(skins_root):
    _make_skin(skins_root, "cat")
    _make_skin(skins_root, "dog")
    assert skins.available_skins() == ["default", "cat", "dog"]


def test_incomplete_skin_is_ignored(skins_root):
    _make_skin(skins_root, "broken", hand=False)   # missing po_hand.png
    assert skins.available_skins() == ["default"]


def test_skin_assets_resolves_user_skin(skins_root):
    _make_skin(skins_root, "cat")
    body, hand = skins.skin_assets("cat")
    assert body.endswith(os.path.join("cat", skins.BODY_FILE))
    assert hand.endswith(os.path.join("cat", skins.HAND_FILE))


def test_skin_assets_unknown_returns_none(skins_root):
    assert skins.skin_assets("ghost") is None


def test_default_assets_point_at_bundled_parts(skins_root):
    body, hand = skins.skin_assets("default")
    assert body.endswith(os.path.join("parts", skins.BODY_FILE))
    assert hand.endswith(os.path.join("parts", skins.HAND_FILE))
