from characters import get
from llm import ChatMessage, _MockClient


def _build_system(character_key: str, lore_text: str = "") -> str:
    ch = get(character_key)
    grounding = ""
    if lore_text:
        grounding = (
            "\n\nGROUNDING:\n- [lore/test.md] " + lore_text.replace("\n", " ")
        )
    return ch.system_prompt + grounding


def test_mock_uses_park_voice_template():
    mock = _MockClient()
    reply = mock.chat([
        ChatMessage("system", _build_system("park", "Park drinks coffee poured four minutes early.")),
        ChatMessage("user", "How do you take your coffee?"),
    ])
    # Park's voice profile uses one of several characteristic openers/closers.
    from llm import _VOICE_PROFILES
    park = _VOICE_PROFILES["park"]
    park_signals = (park["openers"] + park.get("short_openers", [])
                    + park.get("warm_openers", []) + park["closers"])
    assert any(o in reply for o in park_signals)


def test_mock_uses_volkov_voice_template():
    mock = _MockClient()
    reply = mock.chat([
        ChatMessage("system", _build_system("volkov", "Volkov mutters in Russian when systems disappoint him.")),
        ChatMessage("user", "How are you doing?"),
    ])
    from llm import _VOICE_PROFILES
    v = _VOICE_PROFILES["volkov"]
    volkov_signals = (v["openers"] + v.get("short_openers", [])
                      + v.get("warm_openers", []) + v["closers"])
    assert any(o in reply for o in volkov_signals)


def test_mock_no_grounding_returns_no_fact_line():
    mock = _MockClient()
    reply = mock.chat([
        ChatMessage("system", _build_system("mira")),
        ChatMessage("user", "What's the weather?"),
    ])
    # Mira's no_fact fallback contains a specific phrase.
    assert "insufficient prior" in reply or "monitor" in reply


def test_mock_does_not_leak_base_rules_text():
    """Regression: the mock previously grabbed _BASE_RULES bullets."""
    mock = _MockClient()
    reply = mock.chat([
        ChatMessage("system", _build_system("park", "Park manually isolated the coolant loop.")),
        ChatMessage("user", "Tell me about the coolant leak."),
    ])
    assert "Stay in your voice" not in reply
    assert "Refer to other crew" not in reply
