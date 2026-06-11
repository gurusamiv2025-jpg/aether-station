from character_loader import merged_cast
from foundry_iq import get_retriever
from persona_memory import PersonaMemory
from slash import dispatch
from world_sim import StationSim


def _deps():
    return {
        "world_sim": StationSim(),
        "persona_memory": PersonaMemory(),
        "retriever": get_retriever(),
        "cast": merged_cast(),
    }


def test_summary_empty_session_friendly_message():
    res = dispatch("/summary", active_character="park", **_deps())
    assert res is not None
    assert "no session activity" in res.body.lower() or "tick 0" in res.body


def test_summary_includes_persona_notes_when_present():
    deps = _deps()
    deps["persona_memory"].observe("park", "For the record, relief ship Thursday.")
    res = dispatch("/summary", active_character="park", **deps)
    assert "park" in res.body
    assert "relief ship Thursday" in res.body or "Persona notes" in res.body


def test_summary_lists_world_state_when_sim_advanced():
    deps = _deps()
    deps["world_sim"].advance(8)
    res = dispatch("/summary", active_character="park", **deps)
    assert "tick" in res.body.lower() or "Station state" in res.body


def test_summary_help_mentions_command():
    res = dispatch("/help", active_character="park", **_deps())
    assert "/summary" in res.body
