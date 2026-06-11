"""Persona memory tests."""

from persona_memory import MAX_FACTS_PER_CHARACTER, PersonaMemory


def test_for_the_record_records_a_fact():
    pm = PersonaMemory()
    ev = pm.observe("park", "For the record, the relief ship arrives Thursday.")
    assert ev["recorded"] == ["the relief ship arrives Thursday"]
    assert pm.get("park") == ["the relief ship arrives Thursday"]


def test_make_a_note_also_works():
    pm = PersonaMemory()
    ev = pm.observe("volkov", "Make a note: torque value 41 Nm on the manifold.")
    assert ev["recorded"]
    assert "41 Nm" in pm.get("volkov")[0]


def test_facts_are_scoped_per_character():
    pm = PersonaMemory()
    pm.observe("park", "For the record, Park-specific.")
    pm.observe("volkov", "For the record, Volkov-specific.")
    assert pm.get("park") == ["Park-specific"]
    assert pm.get("volkov") == ["Volkov-specific"]


def test_forget_drops_matching_fact():
    pm = PersonaMemory()
    pm.observe("park", "For the record, coffee at oh-six-hundred.")
    pm.observe("park", "For the record, briefing at oh-eight-hundred.")
    ev = pm.observe("park", "Forget the coffee note.")
    assert ev["forgot"] == 1
    facts = pm.get("park")
    assert any("briefing" in f for f in facts)
    assert not any("coffee" in f for f in facts)


def test_clear_notes_wipes_character_only():
    pm = PersonaMemory()
    pm.observe("park", "For the record, A.")
    pm.observe("volkov", "For the record, B.")
    ev = pm.observe("park", "Clear your notes")
    assert ev["cleared"]
    assert pm.get("park") == []
    assert pm.get("volkov") == ["B"]


def test_fact_cap_enforced():
    pm = PersonaMemory()
    for i in range(MAX_FACTS_PER_CHARACTER + 4):
        pm.observe("park", f"For the record, fact number {i}.")
    assert len(pm.get("park")) == MAX_FACTS_PER_CHARACTER


def test_no_op_message_does_nothing():
    pm = PersonaMemory()
    ev = pm.observe("park", "Tell me about the Halberd incident.")
    assert not ev["recorded"]
    assert pm.get("park") == []


def test_render_for_prompt_empty_and_populated():
    pm = PersonaMemory()
    assert "(none)" in pm.render_for_prompt("park")
    pm.observe("park", "For the record, X.")
    assert "X" in pm.render_for_prompt("park")
    assert "PERSONAL NOTES" in pm.render_for_prompt("park")


def test_to_dict_round_trips():
    pm = PersonaMemory()
    pm.observe("park", "For the record, foo.")
    pm.observe("volkov", "For the record, bar.")
    payload = pm.to_dict()
    restored = PersonaMemory.from_dict(payload)
    assert restored.get("park") == ["foo"]
    assert restored.get("volkov") == ["bar"]
