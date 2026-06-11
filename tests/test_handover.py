from handover import detect, render_for_prompt


def test_volkov_defers_hb_441_to_okafor():
    h = detect("volkov", "what's the HB-441 biology signal doing?")
    assert h is not None
    assert h.refer_to == "okafor"


def test_okafor_defers_vitals_to_hua():
    h = detect("okafor", "how is Hua's pulse and heart rate?")
    assert h is not None
    assert h.refer_to == "hua"


def test_park_defers_reactor_to_volkov():
    h = detect("park", "torque value on the LiF-A manifold")
    assert h is not None
    assert h.refer_to == "volkov"


def test_no_handover_when_question_is_in_lane():
    # Volkov asked about reactor stays with volkov.
    h = detect("volkov", "torque value on the LiF-A manifold")
    assert h is None


def test_unrelated_question_returns_none():
    h = detect("park", "tell me a story about coffee")
    assert h is None


def test_render_returns_empty_when_no_suggestion():
    assert render_for_prompt(None) == ""


def test_render_includes_topic_and_specialist():
    h = detect("park", "explain the LiF-A loop weld")
    out = render_for_prompt(h)
    assert "volkov" in out
    assert "engineering" in out.lower() or "coolant" in out.lower()
