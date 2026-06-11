"""Golden Q→A retrieval regression set.

These tests pin the *quality* of TF-IDF retrieval on the current lore
corpus. If anyone edits the lore in a way that breaks these mappings,
the test suite will catch it. Each row says: for query Q, the top-K
results should include passages from one of the listed source files.

Add a new golden row when you add lore. Don't be precious about the
exact ordering — what matters is that the relevant doc gets retrieved
at all within top_k.
"""

import pytest

from foundry_iq import LocalRetriever


GOLDEN = [
    # (query, top_k, must_include_one_of)
    ("LiF-B coolant leak Reactor B 2096",     4, {"lore/incidents/coolant-leak.md"}),
    ("Halberd tug 2093 atmospheric skim",     4, {"lore/incidents/halberd.md"}),
    ("HB-441 EM signal biofilm",              4, {"lore/incidents/hb-441.md"}),
    ("Mira-7 behavioral envelope",            4, {"lore/world/mira-commissioning.md",
                                                  "lore/crew/mira.md"}),
    ("Park Orbital Guard service record",     4, {"lore/crew/park-service.md",
                                                  "lore/crew/park.md"}),
    ("xenobiologist Theia vent organics",     4, {"lore/crew/okafor.md",
                                                  "lore/world/timeline.md"}),
    ("Volkov chief engineer Novosibirsk",     4, {"lore/crew/volkov.md"}),
    ("Lin Hua junior medic Chengdu",          4, {"lore/crew/hua.md"}),
    ("JOSC Orbital Guard supply runs",        4, {"lore/world/factions.md",
                                                  "lore/world/station.md"}),
    ("comms blackout antenna solar particle", 4, {"lore/incidents/comms-blackout.md"}),
]


@pytest.fixture(scope="module")
def retriever():
    return LocalRetriever()


@pytest.mark.parametrize("query,top_k,expected", GOLDEN)
def test_retrieval_returns_a_relevant_source(retriever, query, top_k, expected):
    results = retriever.retrieve(query, top_k=top_k)
    sources = {p.source for p in results}
    overlap = sources & expected
    assert overlap, (
        f"query {query!r} returned {sources!r}, expected at least one of {expected!r}"
    )


def test_retrieval_returns_top_score_above_threshold(retriever):
    """Sanity: top-1 score should be non-trivial for an obviously matching query."""
    results = retriever.retrieve("LiF-B coolant leak Reactor B 2096-02-14", top_k=1)
    assert results
    assert results[0].score > 0.10, f"top score too low: {results[0].score:.3f}"
