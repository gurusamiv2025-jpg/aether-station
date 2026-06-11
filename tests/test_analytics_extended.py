from analytics import Metrics, render_metrics_text


def test_slash_counter_increments():
    m = Metrics()
    m.record_slash("/sitrep")
    m.record_slash("/sitrep")
    m.record_slash("/note")
    assert m.slash_by_command["/sitrep"] == 2
    assert m.slash_by_command["/note"] == 1


def test_tool_counter_increments():
    m = Metrics()
    m.record_tool("telemetry_read")
    m.record_tool("vitals_check")
    assert m.tools_invoked["telemetry_read"] == 1
    assert m.tools_invoked["vitals_check"] == 1


def test_scalar_counters():
    m = Metrics()
    m.record_crisis()
    m.record_crisis()
    m.record_memo()
    m.record_handover()
    assert m.crises_observed == 2
    assert m.memos_recorded == 1
    assert m.handovers_suggested == 1


def test_render_includes_slash_section_when_present():
    from characters import get
    m = Metrics()
    m.record_slash("/sitrep")
    text = render_metrics_text(m, get)
    assert "Slash commands used" in text
    assert "/sitrep" in text


def test_render_includes_tools_section():
    from characters import get
    m = Metrics()
    m.record_tool("telemetry_read")
    text = render_metrics_text(m, get)
    assert "Tools invoked" in text


def test_render_omits_empty_counters():
    from characters import get
    m = Metrics()
    text = render_metrics_text(m, get)
    assert "Slash commands used" not in text
    assert "Tools invoked" not in text
