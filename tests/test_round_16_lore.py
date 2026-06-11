"""The round-16 lore additions are retrievable."""

from foundry_iq import LocalRetriever


def test_josc_charter_retrievable():
    r = LocalRetriever()
    results = r.retrieve("JOSC Article 4 commander authority reactor override", top_k=4)
    assert any("josc-charter" in p.source for p in results)


def test_volkov_tools_retrievable():
    r = LocalRetriever()
    results = r.retrieve("Volkov torque wrench inventory tools", top_k=4)
    assert any("volkov-tools" in p.source for p in results)
