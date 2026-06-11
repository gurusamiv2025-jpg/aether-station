"""Smoke test for `cli.py chat` REPL (piped input)."""

import io
import sys

import cli


def test_chat_quits_cleanly(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("/quit\n"))
    rc = cli.main(["chat", "park", "--no-color"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "REPL" in out


def test_chat_unknown_character(capsys):
    rc = cli.main(["chat", "nobody", "--no-color"])
    assert rc == 2


def test_chat_responds_then_quits(monkeypatch, capsys):
    """Send a normal prompt and a /quit."""
    monkeypatch.setattr("sys.stdin", io.StringIO("What's reactor A at?\n/quit\n"))
    rc = cli.main(["chat", "park", "--no-color"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Cmdr. Yuna Park" in out


def test_chat_slash_command_works(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("/sitrep\n/quit\n"))
    rc = cli.main(["chat", "park", "--no-color"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Station SITREP" in out
    assert "Reactor A" in out
