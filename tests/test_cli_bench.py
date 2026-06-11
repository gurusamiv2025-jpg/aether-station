"""`cli.py bench` smoke test."""

import cli


def test_bench_runs_and_reports_for_built_ins(capsys):
    rc = cli.main(["bench"])
    out = capsys.readouterr().out
    assert rc == 0
    # Header
    assert "character" in out
    assert "in_voice" in out
    # Every built-in character should appear in the table.
    for k in ("park", "okafor", "mira", "volkov", "hua"):
        assert k in out
