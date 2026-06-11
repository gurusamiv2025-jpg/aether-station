from voice_input import mic_button_html


def test_mic_button_html_contains_expected_ids():
    html = mic_button_html("target-div", "btn-mic")
    assert "target-div" in html
    assert "btn-mic" in html
    assert "SpeechRecognition" in html


def test_mic_button_html_has_unsupported_fallback():
    html = mic_button_html("a", "b")
    assert "not supported" in html.lower()
