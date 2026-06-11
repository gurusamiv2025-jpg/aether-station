from foundry_iq import LocalRetriever
from reasoning import build_trace


def test_trace_has_all_five_steps():
    r = LocalRetriever()
    passages = r.retrieve("LiF-B coolant leak", top_k=4)
    trace = build_trace("LiF-B coolant leak", passages)
    assert len(trace) == 5
    labels = [s.label for s in trace]
    assert "1. Intent" in labels[0]
    assert "Query" in labels[1]
    assert "Retrieved" in labels[2]
    assert "Salient facts" in labels[3]
    assert "Character synthesis" in labels[4]


def test_intent_classification_picks_relevant_tags():
    r = LocalRetriever()
    passages = r.retrieve("What happened with the reactor coolant?", top_k=3)
    trace = build_trace("What happened with the reactor coolant?", passages)
    intent_step = trace[0]
    flat = " ".join(intent_step.items).lower()
    assert "technical" in flat or "incident" in flat


def test_handles_empty_passages():
    trace = build_trace("anything", [])
    # Should still produce five structured steps
    assert len(trace) == 5
    # Salient-facts step should note the fallback
    assert any("fall back" in i.lower() or "no high-overlap" in i.lower()
               for i in trace[3].items)
