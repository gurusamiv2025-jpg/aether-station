"""`cli.py lore validate` tests."""

import shutil
from pathlib import Path

import cli


def test_validate_returns_zero_on_clean_corpus(capsys):
    rc = cli.main(["lore", "validate"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "no issues" in out.lower()


def test_validate_detects_missing_h1(tmp_path, monkeypatch, capsys):
    """Point the loader at a tmp corpus with a malformed file."""
    fake = tmp_path / "lore"
    fake.mkdir()
    (fake / "world").mkdir()
    (fake / "world" / "good.md").write_text("# Good\n\nbody.\n")
    (fake / "world" / "bad.md").write_text("no heading here\n")
    # Swap the LORE_DIR for the fake one — cli._lore_dispatch reads it from
    # Path(__file__).parent / "lore", so we monkeypatch Path here.
    import cli as cli_mod
    original = cli_mod.__file__
    monkeypatch.setattr(cli_mod, "__file__", str(tmp_path / "fake_cli.py"))
    rc = cli.main(["lore", "validate"])
    out = capsys.readouterr().out
    monkeypatch.setattr(cli_mod, "__file__", original)
    assert rc == 1
    assert "missing top-level" in out
