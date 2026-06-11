from foundry_iq import LocalRetriever, Passage, get_retriever


def test_local_retriever_loads_corpus():
    r = LocalRetriever()
    assert r._corpus, "lore corpus should not be empty"


def test_retrieves_coolant_leak_passages():
    r = LocalRetriever()
    results = r.retrieve("LiF-B coolant leak Reactor B", top_k=4)
    assert results, "expected matches"
    assert any("coolant-leak.md" in p.source for p in results)


def test_retrieves_halberd_passages():
    r = LocalRetriever()
    results = r.retrieve("Halberd Mining Cooperative tug 2093", top_k=4)
    assert results
    assert any("halberd" in p.source.lower() for p in results)


def test_factory_returns_local_when_unconfigured(monkeypatch):
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_AGENT_ID", raising=False)
    assert get_retriever().name == "local-tfidf"


def test_passage_title_extraction():
    p = Passage(text="# A Heading\n\nbody.", source="lore/world/x.md", score=0.5)
    assert p.title == "A Heading"
