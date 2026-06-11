"""Smoke test for `cli.py doctor`."""

import cli


def test_doctor_returns_zero_on_healthy_install(capsys):
    rc = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert rc == 0, f"doctor returned {rc} — output:\n{out}"
    # Every diagnostic line should be OK.
    assert "FAIL" not in out
    assert "all checks passed" in out


def test_doctor_covers_every_critical_subsystem(capsys):
    cli.main(["doctor"])
    out = capsys.readouterr().out
    # Spot-check that each subsystem reports at least once.
    for marker in ("lore/ corpus", "built-in cast", "YAML loader",
                   "retriever", "LLM backend", "safety",
                   "reasoning trace", "scenarios", "relationships",
                   "transcript round-trip"):
        assert marker in out, f"missing diagnostic line: {marker!r}"
