"""Make sure the round-4 lore additions are findable by the retriever."""

from foundry_iq import LocalRetriever


def test_park_service_record_retrievable():
    r = LocalRetriever()
    results = r.retrieve("Park's Orbital Guard service record", top_k=4)
    assert any("park-service" in p.source for p in results)


def test_comms_blackout_retrievable():
    r = LocalRetriever()
    results = r.retrieve("comms blackout 2095 antenna", top_k=4)
    assert any("comms-blackout" in p.source for p in results)
