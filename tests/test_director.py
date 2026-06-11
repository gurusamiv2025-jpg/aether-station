from director import maybe_event, refusal_event
from world_state import StationLog


def _log_with(*pairs):
    log = StationLog()
    for ch, text in pairs:
        if ch == "user":
            log.add("user", "User", text)
        else:
            log.add(ch, ch.capitalize(), text)
    return log


def test_topic_trigger_fires_when_threshold_met():
    log = _log_with(
        ("user", "Tell me about HB-441."),
        ("okafor", "It is fascinating."),
        ("user", "What is the latest EM data on HB-441?"),
    )
    ev = maybe_event(log.entries, last_event_turn=-10)
    assert ev is not None
    assert "HB-441" in ev.body or "EM" in ev.body
    assert ev.category == "topic"


def test_no_event_below_threshold():
    log = _log_with(("user", "Tell me about HB-441."))
    # Pass a recent last_event_turn so the quiet ping cooldown blocks it too.
    ev = maybe_event(log.entries, last_event_turn=log.entries[-1].turn)
    assert ev is None


def test_quiet_ping_fires_after_long_silence():
    log = StationLog()
    for i in range(10):
        log.add("park", "Park", f"line {i}")
    ev = maybe_event(log.entries, last_event_turn=0)
    assert ev is not None
    # Either a topic match (none in this corpus) or the quiet ping.
    assert ev.category in ("quiet", "topic")


def test_director_respects_recent_event_cooldown():
    log = _log_with(
        ("user", "HB-441 update?"),
        ("okafor", "HB-441 amplitude bump noted."),
    )
    # Pretend an event fired on this very turn.
    ev = maybe_event(log.entries, last_event_turn=log.entries[-1].turn)
    assert ev is None


def test_refusal_event_includes_truncated_query():
    long_q = "x" * 500
    ev = refusal_event(long_q)
    assert ev.category == "refusal"
    assert "Logged" in ev.body
    # Should be truncated with ellipsis.
    assert "..." in ev.body or len(ev.body) < 400


def test_topic_cooldown_prevents_same_topic_back_to_back():
    log = _log_with(
        ("user", "Tell me about HB-441."),
        ("okafor", "It is fascinating."),
        ("user", "What is the latest EM data on HB-441?"),
    )
    cooldowns = {}
    ev1 = maybe_event(log.entries, last_event_turn=-10, topic_cooldowns=cooldowns)
    assert ev1 is not None and "HB-441" in ev1.body
    # Same call again should not refire the same topic immediately.
    log.add("user", "User", "Another HB-441 thought.")
    log.add("okafor", "Okafor", "Yes, HB-441 is curious.")
    ev2 = maybe_event(log.entries, last_event_turn=log.entries[-1].turn - 5, topic_cooldowns=cooldowns)
    # Either a different topic fires or nothing fires -- not the same HB-441 broadcast.
    assert ev2 is None or "HB-441" not in ev2.body
