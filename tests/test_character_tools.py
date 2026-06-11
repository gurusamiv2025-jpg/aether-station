"""Per-character tools tests."""

from character_tools import CHARACTER_TOOLS, detect_and_invoke, render_for_prompt
from world_sim import StationSim


def _sim():
    s = StationSim()
    s.advance(5)
    return s


def test_mira_reads_telemetry_on_status_request():
    sim = _sim()
    results = detect_and_invoke("mira", "give me station status please", sim)
    assert results
    assert any(r.tool == "station_status" for r in results) or any(
        r.tool == "telemetry_read" for r in results
    )


def test_hua_does_vitals_check_on_named_target():
    sim = _sim()
    results = detect_and_invoke("hua", "check on Dr. Okafor's vital signs please", sim)
    assert results
    assert any(r.tool == "vitals_check" for r in results)
    # Okafor's vitals are the one Hua quietly worries about — they're elevated.
    text = " ".join(r.detail for r in results)
    assert "elevated" in text.lower()


def test_volkov_acks_a_reading_and_mutates_world_sim():
    sim = _sim()
    pre = sim.systems["lif_a_psi"].value
    # Move it far from midpoint so ack visibly resets it.
    sim.systems["lif_a_psi"].value = 200.0
    results = detect_and_invoke("volkov", "ack lif a", sim)
    assert results
    assert any(r.tool == "ack_reading" for r in results)
    assert abs(sim.systems["lif_a_psi"].value - 410.0) < 1.0  # midpoint of 390-430


def test_okafor_pulls_hb_441_trend():
    sim = _sim()
    results = detect_and_invoke("okafor", "what's the hb-441 trend right now?", sim)
    assert any(r.tool == "hb441_trend" for r in results)


def test_no_trigger_returns_empty():
    sim = _sim()
    assert detect_and_invoke("park", "tell me a story", sim) == []


def test_render_for_prompt_handles_empty_and_populated():
    assert render_for_prompt([]) == ""
    sim = _sim()
    results = detect_and_invoke("mira", "telemetry", sim)
    block = render_for_prompt(results)
    assert "TOOL RESULTS" in block


def test_every_built_in_character_has_a_tool_catalogue():
    for k in ("park", "okafor", "mira", "volkov", "hua"):
        assert k in CHARACTER_TOOLS
        assert CHARACTER_TOOLS[k], f"{k} has empty catalogue"
