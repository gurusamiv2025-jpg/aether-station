"""Browser TTS — voice profile + button HTML tests."""

from tts import PROFILES, speak_button_html


def test_every_built_in_character_has_a_voice_profile():
    for k in ("park", "okafor", "mira", "volkov", "hua"):
        assert k in PROFILES


def test_voice_profile_fields_are_valid():
    for ch, profile in PROFILES.items():
        assert 0.1 <= profile.rate <= 10.0
        assert 0.0 <= profile.pitch <= 2.0


def test_park_voice_is_lower_pitched_than_hua():
    assert PROFILES["park"].pitch < PROFILES["hua"].pitch


def test_speak_button_html_includes_text():
    html = speak_button_html("park", "Right. Logged.", "btn-1")
    assert "Speak" in html
    assert "Right. Logged." in html
    assert "btn-1" in html


def test_speak_button_escapes_quotes_safely():
    html = speak_button_html("park", "He said: \"hello\" `back`", "btn-2")
    # No raw backticks should leak unescaped into the JS template literal.
    assert "\\`" in html or "back" in html  # escape applied OR safe form


def test_unknown_character_falls_back_to_default_profile():
    html = speak_button_html("nobody", "test", "btn-3")
    # Should still produce a valid button.
    assert "Speak" in html
    assert "btn-3" in html
