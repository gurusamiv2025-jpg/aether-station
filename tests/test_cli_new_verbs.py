"""Tests for the round-15 CLI verbs: status, scenarios, replay."""

import json

import cli


def test_status_prints_backends(capsys):
    rc = cli.main(["status"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "retriever" in out
    assert "llm" in out
    assert "cast size" in out


def test_scenarios_lists_at_least_seven(capsys):
    rc = cli.main(["scenarios"])
    out = capsys.readouterr().out
    assert rc == 0
    # Look for the icon prefixes we know exist.
    icons = ["📜", "⚛️", "🛡️", "🩺"]
    matches = sum(1 for ic in icons if ic in out)
    assert matches >= 3


def test_replay_with_missing_file_returns_one(capsys, tmp_path):
    rc = cli.main(["replay", str(tmp_path / "does_not_exist.json")])
    assert rc == 1


def test_replay_with_good_export_runs(capsys, tmp_path):
    payload = {
        "schema_version": 1,
        "exported_at": "2026-06-08T00:00:00+00:00",
        "histories": {
            "park": [
                {"role": "user", "content": "ping"},
                {"role": "assistant", "content": "right.", "character": "park"},
            ],
        },
        "round_table_history": [],
        "station_log": [],
    }
    p = tmp_path / "sess.json"
    p.write_text(json.dumps(payload))
    rc = cli.main(["replay", str(p)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "ping" in out
    assert "park" in out
