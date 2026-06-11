"""BM25Retriever tests — sanity + golden hits."""

from foundry_iq import BM25Retriever, get_retriever


def test_bm25_finds_coolant_leak():
    r = BM25Retriever()
    results = r.retrieve("LiF-B coolant leak 11 second delay", top_k=4)
    assert results
    assert any("coolant-leak" in p.source for p in results)


def test_bm25_finds_halberd():
    r = BM25Retriever()
    results = r.retrieve("Halberd tug 2093 atmospheric skim", top_k=4)
    assert results
    assert any("halberd" in p.source for p in results)


def test_bm25_scores_normalized_to_top_one():
    r = BM25Retriever()
    results = r.retrieve("Mira-7 station AI", top_k=3)
    assert results
    # Top score should be 1.0 after normalisation, others <= 1.0.
    assert results[0].score == 1.0
    for p in results[1:]:
        assert p.score <= 1.0


def test_bm25_empty_query_returns_empty():
    r = BM25Retriever()
    assert r.retrieve("", top_k=4) == []


def test_factory_returns_bm25_when_env_set(monkeypatch):
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_AGENT_ID", raising=False)
    monkeypatch.setenv("RETRIEVER_BACKEND", "bm25")
    assert get_retriever().name == "bm25"


def test_factory_defaults_to_tfidf(monkeypatch):
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_AGENT_ID", raising=False)
    monkeypatch.delenv("RETRIEVER_BACKEND", raising=False)
    assert get_retriever().name == "local-tfidf"
