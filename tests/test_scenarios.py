from characters import CHARACTERS
from scenarios import SCENARIOS, by_key


def test_at_least_three_scenarios():
    assert len(SCENARIOS) >= 3


def test_every_scenario_targets_a_real_character():
    for sc in SCENARIOS:
        assert sc.active_character in CHARACTERS, sc.key
        if sc.round_table_pair:
            a, b = sc.round_table_pair
            assert a in CHARACTERS and b in CHARACTERS, sc.key
            assert a != b, sc.key


def test_by_key_round_trips():
    for sc in SCENARIOS:
        assert by_key(sc.key) is sc


def test_unknown_scenario_raises():
    import pytest
    with pytest.raises(KeyError):
        by_key("nope")
