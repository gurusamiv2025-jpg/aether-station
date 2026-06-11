from world_state import MAX_LOG_ENTRIES, StationLog, format_for_prompt


def test_add_and_recent():
    log = StationLog()
    log.add("park", "Cmdr. Yuna Park", "Status quo. Reactor A holding.")
    log.add("volkov", "Kostya Volkov", "Eleven seconds. Eleven. I will not let it go.")
    recent = log.recent(n=2)
    assert len(recent) == 2
    assert recent[-1].speaker == "Kostya Volkov"


def test_exclude_character():
    log = StationLog()
    log.add("park", "Cmdr. Yuna Park", "Hello.")
    log.add("volkov", "Kostya Volkov", "Hello back.")
    recent = log.recent(exclude_character="park")
    assert all(e.character != "park" for e in recent)


def test_log_stays_within_max():
    """With the summarizer in play, the log compresses rather than
    sticking to exactly MAX_LOG_ENTRIES, but it must never exceed it."""
    log = StationLog()
    for i in range(MAX_LOG_ENTRIES + 30):
        log.add("park", "Cmdr. Yuna Park", f"line {i}.")
    assert len(log.entries) <= MAX_LOG_ENTRIES
    # Some kind of summary should exist once we cross the trigger.
    assert any(e.is_summary for e in log.entries)


def test_format_for_prompt_empty():
    out = format_for_prompt([])
    assert "none" in out.lower() or "quiet" in out.lower()


def test_format_for_prompt_renders():
    log = StationLog()
    e1 = log.add("park", "Cmdr. Yuna Park", "Status update.")
    out = format_for_prompt([e1])
    assert "Cmdr. Yuna Park" in out
    assert "Status update" in out
