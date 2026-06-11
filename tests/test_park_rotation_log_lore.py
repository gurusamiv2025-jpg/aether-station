from foundry_iq import LocalRetriever


def test_park_rotation_log_retrievable():
    r = LocalRetriever()
    results = r.retrieve("Park personal rotation log entry coffee Mira", top_k=4)
    assert any("park-rotation-log" in p.source for p in results)
