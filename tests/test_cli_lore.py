"""Tests for the `lore` subcommand of cli.py."""

import json

import pytest

import cli


def test_lore_list_includes_every_corpus_file(capsys):
    rc = cli.main(["lore", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    # Spot-check a few files we know exist.
    assert "lore/world/station.md" in out
    assert "lore/incidents/coolant-leak.md" in out
    assert "lore/crew/park.md" in out
    # And the Round-10 addition.
    assert "lore/world/mira-commissioning.md" in out


def test_lore_search_json_returns_passages(capsys):
    rc = cli.main(["lore", "search", "coolant leak", "--top", "3", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) >= 1
    top = data[0]
    assert "source" in top and "score" in top and "preview" in top


def test_lore_stats_prints_counts(capsys):
    rc = cli.main(["lore", "stats"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "files:" in out
    assert "total words:" in out
    assert "by folder:" in out
    # We know we have at least these three folders:
    for folder in ("crew", "incidents", "world"):
        assert folder in out


def test_mira_commissioning_lore_is_retrievable():
    """The Round-10 lore should be findable by the retriever."""
    from foundry_iq import LocalRetriever

    r = LocalRetriever()
    results = r.retrieve("Mira-7 commissioning report behavioral envelope", top_k=4)
    assert any("mira-commissioning" in p.source for p in results)
