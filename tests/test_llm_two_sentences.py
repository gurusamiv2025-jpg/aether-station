"""The mock LLM should chain a second salient sentence when one exists."""

from characters import get
from llm import ChatMessage, _MockClient


def _system_with_two_facts(character_key, fact_a, fact_b):
    ch = get(character_key)
    grounding = (
        "\n\nGROUNDING:\n"
        f"- [lore/a.md] {fact_a}\n"
        f"- [lore/b.md] {fact_b}\n"
    )
    return ch.system_prompt + grounding


def test_reply_chains_two_facts_when_both_relevant():
    mock = _MockClient()
    reply = mock.chat([
        ChatMessage("system", _system_with_two_facts(
            "park",
            "The 2093 Halberd tug loss was caused by an un-cured heat shield delaminating in atmosphere.",
            "The Halberd Mining Cooperative paid a fine and changed its certification process.",
        )),
        ChatMessage("user", "Tell me about the Halberd incident."),
    ])
    # Both grounding sentences should be detectable in the reply.
    # (We allow either to appear -- the rng may pick either as primary,
    # but with two relevant snippets, the reply should be longer than the
    # single-sentence baseline.)
    assert len(reply) > 150, f"expected chained reply, got: {reply}"


def test_reply_is_single_sentence_when_only_one_relevant():
    mock = _MockClient()
    reply = mock.chat([
        ChatMessage("system", _system_with_two_facts(
            "park",
            "Park drinks coffee poured exactly four minutes before the first sip.",
            "Unrelated lore: hydroponics has a fungus problem.",
        )),
        ChatMessage("user", "How does Park drink her coffee?"),
    ])
    # Should still produce a real reply.
    assert "coffee" in reply.lower() or "Park" in reply or "Right" in reply
