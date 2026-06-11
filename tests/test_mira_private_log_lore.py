from foundry_iq import LocalRetriever


def test_mira_private_log_retrievable():
    r = LocalRetriever()
    results = r.retrieve("Mira-7 private observation log crew well-being", top_k=4)
    assert any("mira-private-log" in p.source for p in results)


def test_mira_log_references_eleven_seconds_meta():
    r = LocalRetriever()
    results = r.retrieve("Mira eleven seconds isolation lag eight files", top_k=4)
    assert any("mira-private-log" in p.source for p in results)
