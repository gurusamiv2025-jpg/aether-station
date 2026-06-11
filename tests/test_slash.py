"""Slash command tests."""

from character_loader import merged_cast
from foundry_iq import get_retriever
from persona_memory import PersonaMemory
from slash import dispatch, is_slash, parse
from world_sim import StationSim


def _deps():
    return {
        "world_sim": StationSim(),
        "persona_memory": PersonaMemory(),
        "retriever": get_retriever(),
        "cast": merged_cast(),
    }


def test_is_slash_recognises_leading_slash_only():
    assert is_slash("/help")
    assert is_slash("  /sitrep")
    assert not is_slash("hello /help")
    assert not is_slash("")


def test_parse_extracts_command_and_args():
    assert parse("/lore coolant leak") == ("/lore", "coolant leak")
    assert parse("/help") == ("/help", "")
    assert parse("  /sitrep ") == ("/sitrep", "")


def test_help_returns_command_list():
    r = dispatch("/help", active_character="park", **_deps())
    assert r is not None
    assert r.is_help
    assert "sitrep" in r.body.lower()
    assert "vitals" in r.body.lower()


def test_sitrep_includes_telemetry():
    r = dispatch("/sitrep", active_character="park", **_deps())
    assert "Reactor A output" in r.body
    assert "Crew positions" in r.body or "crew" in r.body.lower()


def test_vitals_default_target_is_okafor():
    r = dispatch("/vitals", active_character="hua", **_deps())
    assert "Okafor" in r.body or "okafor" in r.title.lower()


def test_vitals_with_target_runs_for_that_person():
    r = dispatch("/vitals park", active_character="hua", **_deps())
    assert "park" in r.title.lower() or "Park" in r.body


def test_reactor_focuses_on_reactor_systems():
    r = dispatch("/reactor", active_character="park", **_deps())
    assert "Reactor A output" in r.body


def test_note_records_into_persona_memory():
    deps = _deps()
    r = dispatch("/note bring extra coffee", active_character="park", **deps)
    assert "Recorded" in r.body
    # Verify the note actually landed
    assert any("coffee" in f for f in deps["persona_memory"].get("park"))


def test_forget_drops_matching_note():
    deps = _deps()
    deps["persona_memory"].observe("park", "For the record, bring extra coffee.")
    r = dispatch("/forget coffee", active_character="park", **deps)
    assert "Forgot" in r.body


def test_clear_wipes_active_character_notes():
    deps = _deps()
    deps["persona_memory"].observe("park", "For the record, a.")
    deps["persona_memory"].observe("park", "For the record, b.")
    r = dispatch("/clear", active_character="park", **deps)
    assert "Cleared" in r.body


def test_handover_sets_target():
    r = dispatch("/handover volkov", active_character="park", **_deps())
    assert r.handover_to == "volkov"


def test_handover_unknown_character_reports_error():
    r = dispatch("/handover nobody", active_character="park", **_deps())
    assert r.handover_to is None


def test_unknown_command_returns_help_hint():
    r = dispatch("/bogus", active_character="park", **_deps())
    assert "/help" in r.body


def test_non_slash_returns_none():
    r = dispatch("just a message", active_character="park", **_deps())
    assert r is None
