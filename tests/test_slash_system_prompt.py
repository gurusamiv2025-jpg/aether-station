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


def test_system_prompt_shows_dossier():
    r = dispatch("/system-prompt", active_character="park", **_deps())
    assert r is not None
    assert "You are Cmdr. Yuna Park" in r.body


def test_system_prompt_unknown_character_friendly():
    deps = _deps()
    r = dispatch("/system-prompt", active_character="nobody", **deps)
    assert r is not None
    assert "no active character" in r.body.lower() or "nobody" in r.body


def test_help_mentions_system_prompt():
    r = dispatch("/help", active_character="park", **_deps())
    assert "/system-prompt" in r.body
