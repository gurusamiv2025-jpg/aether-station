"""Tests for the YAML extra-character loader."""

import os
from pathlib import Path

import pytest

from character_loader import load_extras, merged_cast, merged_voice_profiles
from characters import CHARACTERS


def test_built_in_cast_unchanged_by_loader():
    cast = merged_cast()
    # Every built-in must still be present.
    for k in CHARACTERS:
        assert k in cast


def test_garcia_yaml_loads():
    extras = load_extras()
    keys = [e.character.key for e in extras]
    assert "garcia" in keys, f"expected garcia in extras, got {keys}"


def test_garcia_has_voice_profile():
    profiles = merged_voice_profiles()
    assert "garcia" in profiles
    assert "openers" in profiles["garcia"]


def test_loader_returns_empty_when_dir_missing(tmp_path, monkeypatch):
    import character_loader
    monkeypatch.setattr(character_loader, "EXTRA_DIR", tmp_path / "nope")
    assert character_loader.load_extras() == []


def test_loader_skips_invalid_yaml(tmp_path, monkeypatch):
    import character_loader
    (tmp_path / "broken.yaml").write_text("not: valid: yaml: ::: :")
    (tmp_path / "missing-fields.yaml").write_text("key: justakey\n")
    monkeypatch.setattr(character_loader, "EXTRA_DIR", tmp_path)
    # Should not raise — just return what's salvageable (nothing here).
    assert character_loader.load_extras() == []
