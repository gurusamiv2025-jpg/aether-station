from world_sim import StationSim, SystemReading


def test_sim_starts_with_known_systems():
    s = StationSim()
    assert "reactor_a_mw" in s.systems
    assert "hb441_em_hz" in s.systems
    assert s.tick == 0


def test_advance_increments_tick():
    s = StationSim()
    s.advance(steps=3)
    assert s.tick == 3


def test_render_includes_telemetry_and_positions():
    s = StationSim()
    block = s.render_for_prompt()
    assert "LIVE STATION TELEMETRY" in block
    assert "CREW POSITIONS" in block
    assert "Reactor A output" in block
    assert "park" in block.lower()


def test_headline_changes_when_out_of_nominal():
    s = StationSim()
    r = s.systems["reactor_a_mw"]
    r.value = 0.5  # below nominal_low
    h = s.headline()
    assert "Reactor A output" in h


def test_ack_resets_to_midpoint():
    s = StationSim()
    r = s.systems["lif_a_psi"]
    r.value = 200.0
    s.ack("lif_a_psi")
    mid = (r.nominal_low + r.nominal_high) / 2
    assert abs(r.value - mid) < 0.01


def test_status_label_categories():
    r = SystemReading("x", 100, "u", 50, 60)
    assert r.status == "above nominal"
    r.value = 25
    assert r.status == "below nominal"
    r.value = 55
    assert r.status == "nominal"


def test_to_dict_round_trippable():
    s = StationSim()
    s.advance(5)
    d = s.to_dict()
    assert d["tick"] == 5
    assert "reactor_a_mw" in d["systems"]
