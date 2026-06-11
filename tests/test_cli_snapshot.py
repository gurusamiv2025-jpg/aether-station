"""`cli.py snapshot` smoke test."""

import cli


def test_snapshot_runs_and_includes_cast_lore_doctor(capsys):
    rc = cli.main(["snapshot"])
    out = capsys.readouterr().out
    assert rc == 0
    # Sections
    assert "Cast" in out
    assert "Lore corpus" in out
    assert "Backends" in out
    assert "Live world" in out
    assert "Scenarios available" in out
    assert "Doctor" in out
    # Sentinel values
    assert "park" in out
    assert "Reactor A" in out
    assert "all checks passed" in out
