"""cli.py smoke — exercises the canonical demo path end-to-end."""

import cli


def test_smoke_passes_all_eight_steps(capsys):
    rc = cli.main(["smoke"])
    out = capsys.readouterr().out
    assert rc == 0, f"smoke returned {rc}:\n{out}"
    assert "all 8 demo-path steps PASS" in out


def test_smoke_covers_all_named_steps(capsys):
    cli.main(["smoke"])
    out = capsys.readouterr().out
    for needle in (
        "safety refusal",
        "grounded ask",
        "character tools",
        "handover",
        "crisis routing",
        "inter-character dialogue",
        "/summary slash",
        "state persistence",
    ):
        assert needle in out, f"missing step: {needle!r}"
