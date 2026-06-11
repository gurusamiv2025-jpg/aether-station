import time

from perf import Timings, timer


def test_timer_records_at_least_a_ms():
    t = Timings()
    with timer(t, "x"):
        time.sleep(0.001)
    assert t.samples["x"], "no sample recorded"
    assert t.samples["x"][0] >= 0.5  # at least 0.5ms


def test_stats_for_known_label():
    t = Timings()
    for ms in (10.0, 20.0, 30.0, 40.0, 50.0):
        t.record("op", ms)
    s = t.stats("op")
    assert s["count"] == 5
    assert s["min"] == 10.0
    assert s["max"] == 50.0
    assert 25.0 <= s["avg"] <= 35.0


def test_unknown_label_stats_are_zero():
    t = Timings()
    s = t.stats("nope")
    assert s["count"] == 0
    assert s["max"] == 0.0


def test_cap_per_label_truncates():
    t = Timings(cap_per_label=10)
    for i in range(25):
        t.record("op", float(i))
    assert len(t.samples["op"]) == 10
    # Should keep the newest values (15..24)
    assert min(t.samples["op"]) == 15.0


def test_render_includes_label():
    t = Timings()
    with timer(t, "retrieval"):
        pass
    rendered = t.render()
    assert "retrieval" in rendered
    assert "ms" in rendered
