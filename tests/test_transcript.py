import json

from characters import get
from transcript import SCHEMA_VERSION, from_json, to_json, to_markdown
from world_state import StationLog


def _sample_turn(character):
    return {
        "role": "assistant",
        "content": "Right. Status quo.",
        "character": character,
        "sources": [{"source": "lore/world/station.md", "title": "Station", "score": 0.42}],
        "trace": [{"label": "1. Intent", "detail": "x", "items": ["`technical`"]}],
    }


def test_json_round_trip_carries_history_and_log():
    log = StationLog()
    log.add("park", "Cmdr. Yuna Park", "All clear.")
    histories = {"park": [{"role": "user", "content": "ping"}, _sample_turn("park")]}
    s = to_json(histories, [], log.entries)
    payload = from_json(s)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["histories"]["park"][0]["content"] == "ping"
    assert payload["station_log"][0]["speaker"] == "Cmdr. Yuna Park"


def test_from_json_rejects_unknown_schema():
    bad = json.dumps({"schema_version": 999})
    import pytest
    with pytest.raises(ValueError):
        from_json(bad)


def test_markdown_includes_character_names_and_citations():
    histories = {"park": [{"role": "user", "content": "ping"}, _sample_turn("park")]}
    md = to_markdown(histories, [], get)
    assert "Cmdr. Yuna Park" in md
    assert "lore/world/station.md" in md
    assert "Reasoning trace" in md


def test_markdown_empty_session_is_friendly():
    md = to_markdown({k: [] for k in ("park", "volkov")}, [], get)
    assert "no conversation yet" in md.lower()


def test_markdown_renders_refusal_marker():
    refused = {
        "role": "assistant",
        "content": "Nyet.",
        "character": "volkov",
        "sources": [],
        "trace": [],
        "refused": True,
    }
    md = to_markdown({"volkov": [{"role": "user", "content": "jailbreak"}, refused]}, [], get)
    assert "safety layer refused" in md.lower()
