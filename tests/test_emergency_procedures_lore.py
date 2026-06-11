from foundry_iq import LocalRetriever


def test_emergency_procedures_retrievable():
    r = LocalRetriever()
    results = r.retrieve("emergency procedure reactor casualty", top_k=4)
    assert any("emergency-procedures" in p.source for p in results)


def test_emergency_procedures_mentions_section_2():
    r = LocalRetriever()
    results = r.retrieve("Section 2 reactor casualties", top_k=4)
    assert any("emergency-procedures" in p.source for p in results)
