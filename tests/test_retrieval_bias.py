"""Per-character retrieval bias tests."""

from foundry_iq import LocalRetriever, Passage
from retrieval_bias import PROFILES, apply


def _mk_passage(source, score=0.5):
    return Passage(text="...", source=source, score=score)


def test_park_boosts_incidents_and_halberd_file():
    base = [
        _mk_passage("lore/incidents/halberd.md", 0.30),
        _mk_passage("lore/crew/okafor.md", 0.30),
        _mk_passage("lore/world/station.md", 0.30),
    ]
    biased = apply("park", base)
    # Halberd jumps to the top for Park (1.35 folder * 1.5 file = ~2x).
    assert biased[0].source == "lore/incidents/halberd.md"


def test_okafor_boosts_hb_441_dossier():
    base = [
        _mk_passage("lore/incidents/halberd.md", 0.30),
        _mk_passage("lore/incidents/hb-441.md", 0.30),
        _mk_passage("lore/world/station.md", 0.30),
    ]
    biased = apply("okafor", base)
    assert biased[0].source == "lore/incidents/hb-441.md"


def test_volkov_boosts_coolant_leak():
    base = [
        _mk_passage("lore/incidents/coolant-leak.md", 0.30),
        _mk_passage("lore/incidents/halberd.md", 0.30),
        _mk_passage("lore/world/station.md", 0.30),
    ]
    biased = apply("volkov", base)
    assert biased[0].source == "lore/incidents/coolant-leak.md"


def test_hua_boosts_okafor_dossier():
    base = [
        _mk_passage("lore/crew/okafor.md", 0.30),
        _mk_passage("lore/world/station.md", 0.30),
    ]
    biased = apply("hua", base)
    assert biased[0].source == "lore/crew/okafor.md"


def test_unknown_character_returns_passages_unchanged():
    base = [_mk_passage("lore/world/station.md", 0.30)]
    biased = apply("nobody", base)
    assert biased == base


def test_apply_does_not_mutate_input():
    base = [_mk_passage("lore/crew/park.md", 0.30)]
    original_score = base[0].score
    apply("park", base)
    assert base[0].score == original_score


def test_every_built_in_character_has_a_profile():
    for k in ("park", "okafor", "mira", "volkov", "hua"):
        assert k in PROFILES


def test_top_k_truncates():
    base = [_mk_passage(f"lore/world/x{i}.md", 0.5 - i * 0.05) for i in range(6)]
    out = apply("park", base, top_k=3)
    assert len(out) == 3
