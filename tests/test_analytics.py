from analytics import Metrics, render_metrics_text
from characters import get


def _grounded_turn(character_key, source, score):
    return {
        "role": "assistant",
        "content": "...",
        "character": character_key,
        "sources": [{"source": source, "title": "x", "score": score}],
        "trace": [],
    }


def _refused_turn(character_key, category):
    return {
        "role": "assistant",
        "content": "no.",
        "character": character_key,
        "sources": [],
        "trace": [{"label": "Safety layer", "detail": f"Input flagged as `{category}` — refused."}],
        "refused": True,
    }


def test_records_queries_and_citations():
    m = Metrics()
    m.record_turn("park", _grounded_turn("park", "lore/world/station.md", 0.4))
    m.record_turn("park", _grounded_turn("park", "lore/world/station.md", 0.6))
    m.record_turn("volkov", _grounded_turn("volkov", "lore/incidents/coolant-leak.md", 0.5))
    assert m.total_queries() == 3
    assert m.queries_by_character["park"] == 2
    top = m.top_citations(5)
    assert top[0][0] == "lore/world/station.md"
    assert top[0][1] == 2
    assert abs(top[0][2] - 0.5) < 0.001


def test_records_refusals_by_category():
    m = Metrics()
    m.record_turn("park", _refused_turn("park", "jailbreak"))
    m.record_turn("volkov", _refused_turn("volkov", "harm"))
    m.record_turn("park", _refused_turn("park", "jailbreak"))
    assert m.total_refusals() == 3
    assert m.refusals_by_category["jailbreak"] == 2
    assert m.refusals_by_category["harm"] == 1


def test_avg_score_per_character():
    m = Metrics()
    m.record_turn("park", _grounded_turn("park", "x.md", 0.2))
    m.record_turn("park", _grounded_turn("park", "y.md", 0.4))
    assert abs(m.avg_score_for("park") - 0.3) < 0.001
    assert m.avg_score_for("hua") == 0.0


def test_render_metrics_text_is_markdown_safe():
    m = Metrics()
    m.record_turn("park", _grounded_turn("park", "lore/world/station.md", 0.4))
    text = render_metrics_text(m, get)
    assert "Total queries" in text
    assert "Cmdr. Yuna Park" in text
    assert "lore/world/station.md".replace("lore/", "") in text
