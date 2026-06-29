"""Tests for persistent settings (issues #4/#5: scale, skin, follow-mouse)."""
import json
import os

import pytest

from src import settings


@pytest.fixture(autouse=True)
def _temp_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("PO_SETTINGS_PATH", str(tmp_path / "settings.json"))


def test_load_returns_defaults_when_missing():
    assert settings.load() == settings.DEFAULTS


def test_save_then_load_roundtrip():
    settings.save(scale=1.25, skin="cat", follow_mouse=False)
    got = settings.load()
    assert got == {"scale": 1.25, "skin": "cat", "follow_mouse": False}


def test_save_merges_without_dropping_other_keys():
    settings.save(skin="dog")
    settings.save(scale=0.75)
    got = settings.load()
    assert got["skin"] == "dog" and got["scale"] == 0.75


def test_scale_is_clamped_to_bounds():
    assert settings.save(scale=9.0)["scale"] == settings.SCALE_MAX
    assert settings.save(scale=0.01)["scale"] == settings.SCALE_MIN


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = os.environ["PO_SETTINGS_PATH"]
    with open(path, "w") as f:
        f.write("{ not valid json")
    assert settings.load() == settings.DEFAULTS


def test_invalid_types_are_coerced():
    path = os.environ["PO_SETTINGS_PATH"]
    with open(path, "w") as f:
        json.dump({"scale": "big", "skin": 123, "follow_mouse": "yes"}, f)
    got = settings.load()
    assert got["scale"] == settings.DEFAULTS["scale"]
    assert got["skin"] == "default"
    assert got["follow_mouse"] is True
