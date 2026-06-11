"""Round-trip persistence tests."""

import tempfile

from audit import AuditLog
from memo import MemoBook
from mood import MoodState
from persistence import (
    SCHEMA_VERSION,
    apply,
    read_from,
    serialize,
    write_to,
)
from persona_memory import PersonaMemory
from world_sim import StationSim


def _populated_state():
    sim = StationSim()
    sim.advance(7)
    sim.systems["lif_a_psi"].value = 200.0
    pm = PersonaMemory()
    pm.observe("park", "For the record, the relief ship arrives Thursday.")
    ms = MoodState()
    ms.observe("volkov", "the lif-b coolant leak again")
    al = AuditLog()
    al.safety("park", "jailbreak", allowed=False)
    mb = MemoBook()
    mb.record_turn("park", {"role": "assistant", "content": "first"})
    return sim, pm, ms, al, mb


def test_serialize_then_apply_round_trips():
    sim, pm, ms, al, mb = _populated_state()
    blob = serialize(world_sim=sim, persona_memory=pm,
                     mood_state=ms, audit_log=al, memo_book=mb)
    import json
    payload = json.loads(blob)
    assert payload["schema_version"] == SCHEMA_VERSION
    restored = apply(payload, world_sim_cls=StationSim,
                     persona_memory_cls=PersonaMemory,
                     mood_state_cls=MoodState,
                     audit_log_cls=AuditLog,
                     memo_book_cls=MemoBook)
    assert restored["world_sim"].tick == 7
    assert abs(restored["world_sim"].systems["lif_a_psi"].value - 200.0) < 0.01
    assert restored["persona_memory"].get("park") == [
        "the relief ship arrives Thursday"
    ]
    assert "volkov" in restored["mood_state"].moods
    assert len(restored["audit_log"]) == 1
    assert len(restored["memo_book"]) == 1


def test_write_then_read_via_file(tmp_path):
    sim, pm, ms, al, mb = _populated_state()
    p = tmp_path / "session.json"
    write_to(p, world_sim=sim, persona_memory=pm,
             mood_state=ms, audit_log=al, memo_book=mb)
    assert p.exists()
    payload = read_from(p)
    assert payload["schema_version"] == SCHEMA_VERSION


def test_unsupported_schema_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text('{"schema_version": 999}')
    import pytest
    with pytest.raises(ValueError):
        read_from(p)


def test_apply_preserves_memo_dedup_seen_set():
    """Memo `_seen` set must be restored so re-recording the same kind no-ops."""
    sim, pm, ms, al, mb = _populated_state()
    mb.record_crisis_first("LiF-A")
    blob = serialize(world_sim=sim, persona_memory=pm,
                     mood_state=ms, audit_log=al, memo_book=mb)
    import json
    payload = json.loads(blob)
    restored = apply(payload, world_sim_cls=StationSim,
                     persona_memory_cls=PersonaMemory,
                     mood_state_cls=MoodState,
                     audit_log_cls=AuditLog,
                     memo_book_cls=MemoBook)
    # Re-recording crisis on the restored memo book should not add a duplicate.
    assert not restored["memo_book"].record_crisis_first("LiF-A again")
