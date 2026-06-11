"""Conversation summarizer tests."""

from world_state import (
    MAX_LOG_ENTRIES,
    SUMMARY_KEEP_RECENT,
    SUMMARY_TRIGGER,
    StationLog,
)


def test_no_summary_below_trigger():
    log = StationLog()
    for i in range(SUMMARY_TRIGGER):
        log.add("park", "Park", f"turn {i}")
    assert all(not e.is_summary for e in log.entries)


def test_summary_fires_above_trigger():
    log = StationLog()
    for i in range(SUMMARY_TRIGGER + 5):
        log.add("park", "Park", f"turn {i}")
    summaries = [e for e in log.entries if e.is_summary]
    assert len(summaries) >= 1
    # Recent verbatim turns should still be present.
    non_summary = [e for e in log.entries if not e.is_summary]
    assert len(non_summary) >= SUMMARY_KEEP_RECENT


def test_only_one_rollup_after_many_turns():
    log = StationLog()
    for i in range(50):
        log.add("park", "Park", f"turn {i}")
    summaries = [e for e in log.entries if e.is_summary]
    # We merge into one rolling summary, not a stack.
    assert len(summaries) == 1


def test_summary_speaker_label():
    log = StationLog()
    for i in range(SUMMARY_TRIGGER + 5):
        log.add("park", "Park", f"turn {i}")
    sums = [e for e in log.entries if e.is_summary]
    assert sums[0].speaker == "Earlier in this session"


def test_log_stays_within_max_entries():
    log = StationLog()
    for i in range(80):
        log.add("park", "Park", f"turn {i}")
    assert len(log.entries) <= MAX_LOG_ENTRIES
