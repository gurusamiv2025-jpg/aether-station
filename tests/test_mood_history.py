"""Mood history tests (round 17.3)."""

from mood import MoodState


def test_history_appended_on_observe():
    ms = MoodState()
    ms.observe("park", "coffee please")
    ms.observe("park", "tell me about Park's coffee habit")
    assert "park" in ms.history
    assert len(ms.history["park"]) == 2
    snap = ms.history["park"][-1]
    for key in ("turn", "energy", "focus", "openness"):
        assert key in snap


def test_history_caps_at_200_per_character():
    ms = MoodState()
    for i in range(220):
        ms.observe("park", f"line {i}")
    assert len(ms.history["park"]) == 200


def test_history_is_per_character():
    ms = MoodState()
    ms.observe("park", "anything")
    ms.observe("volkov", "anything")
    assert "park" in ms.history
    assert "volkov" in ms.history
    assert ms.history["park"] != ms.history["volkov"]
