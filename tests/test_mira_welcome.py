from mira_welcome import WELCOME_LINES, build_welcome_turn


def test_welcome_turn_marked_and_in_voice():
    turn = build_welcome_turn()
    assert turn["is_welcome"] is True
    assert turn["character"] == "mira"
    assert turn["role"] == "assistant"
    # Mira's signature sign-off
    assert "Logged." in turn["content"]


def test_welcome_mentions_every_built_in_character():
    body = build_welcome_turn()["content"]
    for needle in ("Park", "Okafor", "HB-441", "Volkov", "Lin Hua"):
        assert needle in body
