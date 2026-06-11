from audit import AuditEntry, AuditLog


def test_safety_event_records_kind():
    log = AuditLog()
    log.safety("park", "jailbreak", allowed=False)
    assert len(log) == 1
    assert log.entries[0].kind == "refusal"


def test_safety_allowed_uses_safety_kind():
    log = AuditLog()
    log.safety("park", "", allowed=True)
    assert log.entries[0].kind == "safety"


def test_memory_event_skips_no_op():
    log = AuditLog()
    log.memory_event("park", {"recorded": [], "forgot": 0, "cleared": False})
    assert len(log) == 0


def test_memory_event_records_changes():
    log = AuditLog()
    log.memory_event("park", {"recorded": ["X"], "forgot": 0, "cleared": False})
    assert len(log) == 1
    assert "recorded=1" in log.entries[0].detail


def test_dialogue_start_records_topic_and_rounds():
    log = AuditLog()
    log.dialogue_start("park", "volkov", "HB-441", 2)
    e = log.entries[0]
    assert e.kind == "dialogue"
    assert "HB-441" in e.detail
    assert "rounds=2" in e.detail


def test_to_csv_has_header_and_rows():
    log = AuditLog()
    log.safety("park", "jailbreak", allowed=False)
    csv = log.to_csv()
    assert csv.startswith("timestamp,kind,character,summary,detail")
    assert "park" in csv


def test_by_kind_filters():
    log = AuditLog()
    log.safety("park", "jailbreak", allowed=False)
    log.safety("park", "", allowed=True)
    log.dialogue_start("park", "volkov", "x", 1)
    assert len(log.by_kind("refusal")) == 1
    assert len(log.by_kind("dialogue")) == 1
