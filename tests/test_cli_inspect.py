"""cli.py inspect tests."""

import cli


def test_inspect_park_prints_dossier(capsys):
    rc = cli.main(["inspect", "park"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Cmdr. Yuna Park" in out
    assert "System prompt" in out
    assert "Voice profile" in out
    assert "Address forms" in out
    assert "Retrieval bias" in out


def test_inspect_unknown_returns_nonzero(capsys):
    rc = cli.main(["inspect", "nobody"])
    assert rc == 1


def test_inspect_includes_tools_when_present(capsys):
    rc = cli.main(["inspect", "mira"])
    out = capsys.readouterr().out
    assert "Tools available" in out
