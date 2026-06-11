from mood import Mood, MoodState, style_bias_from_mood


def test_mood_starts_at_max():
    m = Mood()
    assert m.energy == 1.0 and m.focus == 1.0 and m.openness == 1.0
    assert "steady" in m.label() or "fresh" in m.label() or "calm" in m.label()


def test_topic_lowers_focus_for_volkov():
    ms = MoodState()
    before = ms.get("volkov").focus
    ms.observe("volkov", "the LiF-B coolant leak on Reactor B")
    after = ms.get("volkov").focus
    assert after < before


def test_topic_does_not_affect_other_characters():
    ms = MoodState()
    park_before = ms.get("park").focus
    ms.observe("volkov", "LiF-B coolant leak")
    park_after = ms.get("park").focus
    assert park_after == park_before


def test_clamp_within_bounds():
    m = Mood(energy=2.0, focus=-1.0, openness=0.5)
    m.clamp()
    assert 0.0 <= m.energy <= 1.0
    assert 0.0 <= m.focus <= 1.0


def test_label_changes_when_stressed():
    m = Mood(energy=0.2, focus=0.2, openness=0.2)
    assert "tired" in m.label()
    assert "stressed" in m.label()
    assert "curt" in m.label()


def test_render_for_prompt_includes_label_and_hint():
    ms = MoodState()
    block = ms.render_for_prompt("park")
    assert "CURRENT MOOD" in block
    assert "do not announce" in block.lower()


def test_refusal_tightens_mood():
    ms = MoodState()
    before = ms.get("park").focus
    ms.observe("park", "anything", is_refusal=True)
    assert ms.get("park").focus < before


def test_style_bias_reflects_mood():
    bias = style_bias_from_mood(Mood(focus=0.2, openness=0.2))
    assert bias["prefer_short"] is True
    bias_warm = style_bias_from_mood(Mood(openness=0.9))
    assert bias_warm["prefer_warm"] is True
