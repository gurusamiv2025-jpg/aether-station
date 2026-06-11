from transcript import apply_to_state, from_json, to_json
from world_state import StationLog


def test_apply_to_state_round_trips_log_and_history():
    log = StationLog()
    log.add("park", "Cmdr. Yuna Park", "Status quo.")
    log.add("volkov", "Kostya Volkov", "Eleven seconds.")
    histories = {"park": [{"role": "user", "content": "hi"}]}
    rt = []
    data = to_json(histories, rt, log.entries)
    payload = from_json(data)
    applied = apply_to_state(payload, StationLog)
    assert applied["histories"]["park"][0]["content"] == "hi"
    assert applied["round_table_history"] == []
    new_log = applied["station_log"]
    assert len(new_log.entries) == 2
    assert new_log.entries[0].speaker == "Cmdr. Yuna Park"


def test_apply_to_state_handles_missing_fields():
    payload = {"schema_version": 1}
    applied = apply_to_state(payload, StationLog)
    assert applied["histories"] == {}
    assert applied["round_table_history"] == []
    assert len(applied["station_log"].entries) == 0
