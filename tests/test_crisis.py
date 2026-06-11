from crisis import CrisisEvent, owner, render_for_prompt, scan
from world_sim import StationSim


def _sim_with(key, value):
    s = StationSim()
    s.systems[key].value = value
    return s


def test_no_crisis_at_nominal():
    s = StationSim()
    assert scan(s) == []


def test_lif_a_low_triggers_volkov_owned_alarm():
    s = _sim_with("lif_a_psi", 200.0)
    events = scan(s)
    assert len(events) == 1
    assert events[0].owner_key == "volkov"
    assert events[0].status == "below nominal"


def test_o2_low_routes_to_mira():
    s = _sim_with("o2_ring3_kpa", 16.0)
    events = scan(s)
    assert any(e.owner_key == "mira" for e in events)


def test_hb441_high_routes_to_okafor():
    s = _sim_with("hb441_em_hz", 0.10)
    events = scan(s)
    assert any(e.owner_key == "okafor" and e.system_key == "hb441_em_hz" for e in events)


def test_severity_grows_with_distance():
    near = _sim_with("lif_a_psi", 386.0)  # just below
    far = _sim_with("lif_a_psi", 200.0)   # way below
    near_severity = scan(near)[0].severity
    far_severity = scan(far)[0].severity
    assert (near_severity, far_severity) == ("watch", "alarm")


def test_render_includes_system_name_and_owner():
    events = scan(_sim_with("lif_a_psi", 200.0))
    block = render_for_prompt(events)
    assert "LiF-A loop pressure" in block
    assert "volkov" in block


def test_owner_lookup_falls_back_to_park():
    assert owner("unknown_system") == "park"
