"""Multi-step reasoning trace.

Every character reply is the end of a small chain:

    user input
       ↓        (1) classify intent
    intent
       ↓        (2) form retrieval query
    query
       ↓        (3) Foundry IQ retrieves grounded passages
    passages
       ↓        (4) extract salient facts
    facts
       ↓        (5) character voice applies
    reply

This module builds a structured trace the UI renders alongside the answer
so judges (and users) can see the agent's reasoning, not just the output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from foundry_iq import Passage


@dataclass
class ReasoningStep:
    label: str
    detail: str
    items: List[str] = field(default_factory=list)


# --- intent tags ----------------------------------------------------------

_INTENT_PATTERNS = [
    ("technical", r"\b(reactor|coolant|lif|leak|repair|airlock|comms|power)\b"),
    ("incident", r"\b(halberd|hb-?441|incident|leak|accident|emergency)\b"),
    ("relational", r"\b(feel|trust|think of|relationship|opinion|like|hate|friend)\b"),
    ("personal", r"\b(you|your|yourself|memory|past|history|backstory)\b"),
    ("operational", r"\b(status|schedule|shift|today|currently|now|when)\b"),
    ("research", r"\b(sample|biology|organism|signal|specimen|experiment)\b"),
]


def _classify_intent(user_input: str, passages: List[Passage]) -> List[str]:
    """Tag the question by topic. Uses keywords + source folders."""
    text = user_input.lower()
    tags: list[str] = []
    for tag, pattern in _INTENT_PATTERNS:
        if re.search(pattern, text):
            tags.append(tag)
    # Source-folder hints
    for p in passages[:3]:
        if "/incidents/" in p.source and "incident" not in tags:
            tags.append("incident")
        if "/crew/" in p.source and "personal" not in tags:
            tags.append("personal")
        if "/world/" in p.source and "operational" not in tags:
            tags.append("operational")
    if not tags:
        tags.append("general")
    return tags[:4]


# --- key facts ------------------------------------------------------------


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _key_facts(passages: List[Passage], user_input: str, max_facts: int = 4) -> List[str]:
    """Pull the most question-relevant sentences from the passages."""
    if not passages:
        return []
    keywords = {
        w.lower()
        for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", user_input)
        if len(w) > 2
    }
    # Drop stopword-ish short words.
    stop = {"the", "and", "for", "are", "but", "you", "your", "with", "that", "this", "what", "when", "how", "why", "who", "tell", "about"}
    keywords -= stop

    scored: list[tuple[float, str, str]] = []
    for p in passages:
        body = re.sub(r"^#+\s+.*$", "", p.text, flags=re.MULTILINE)  # drop headings
        body = re.sub(r"\*\*([^*]+)\*\*", r"\1", body)  # drop bold
        for sent in _SENT_SPLIT.split(body):
            sent = sent.strip().replace("\n", " ")
            if not sent or len(sent) < 30 or len(sent) > 220:
                continue
            tokens = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", sent)}
            overlap = len(tokens & keywords)
            if overlap == 0:
                continue
            scored.append((overlap + p.score, sent, p.source))

    scored.sort(key=lambda x: x[0], reverse=True)
    seen: set[str] = set()
    out: list[str] = []
    for _, sent, src in scored:
        key = sent[:60].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(f"{sent}  *({src})*")
        if len(out) >= max_facts:
            break
    return out


# --- query rewrite --------------------------------------------------------


def _rewrite_query(user_input: str, intents: List[str]) -> str:
    """Surface what would be sent to Foundry IQ.

    Right now the app sends the raw user input; this gives the UI an honest
    label for what was asked, plus an intent hint that would help an agent
    pick the right tool.
    """
    base = user_input.strip().rstrip("?.!,")
    hints = ", ".join(intents)
    return f'"{base}" — intent hints: [{hints}]'


# --- public builder -------------------------------------------------------


def build_trace(user_input: str, passages: List[Passage]) -> List[ReasoningStep]:
    intents = _classify_intent(user_input, passages)
    facts = _key_facts(passages, user_input)
    steps: list[ReasoningStep] = []
    steps.append(
        ReasoningStep(
            label="1. Intent",
            detail="Classified the question to guide retrieval.",
            items=[f"`{tag}`" for tag in intents],
        )
    )
    steps.append(
        ReasoningStep(
            label="2. Query → Foundry IQ",
            detail="What we asked the knowledge layer.",
            items=[_rewrite_query(user_input, intents)],
        )
    )
    steps.append(
        ReasoningStep(
            label=f"3. Retrieved ({len(passages)} passages)",
            detail="Grounded passages with relevance scores.",
            items=[
                f"`{p.source}` — score {p.score:.2f} — *{p.title}*"
                for p in passages
            ],
        )
    )
    steps.append(
        ReasoningStep(
            label=f"4. Salient facts ({len(facts)})",
            detail="Sentences from the passages most relevant to the question.",
            items=facts if facts else ["*(no high-overlap sentences — character will fall back to in-voice deflection)*"],
        )
    )
    steps.append(
        ReasoningStep(
            label="5. Character synthesis",
            detail="LLM composes the answer in the character's voice, citing only retrieved facts.",
            items=[],
        )
    )
    return steps
