"""cli.py crisis smoke."""

import cli


def test_crisis_for_known_system_returns_zero(capsys):
    rc = cli.main(["crisis", "lif_a_psi", "--value", "200"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "LiF-A loop pressure" in out
    assert "volkov" in out
    assert "below nominal" in out


def test_crisis_for_unknown_system_returns_one(capsys):
    rc = cli.main(["crisis", "no_such_system"])
    assert rc == 1


def test_crisis_routes_o2_to_mira(capsys):
    rc = cli.main(["crisis", "o2_ring3_kpa", "--value", "16"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Mira-7" in out  # Mira owns life support
