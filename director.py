"""Director agent — ambient station events.

A 6th invisible agent that watches the conversation pattern and, when
the right signal appears, injects a short Mira-7 broadcast or an
in-world event into the chat. This turns the chatbot from a five-window
chat into a living station where things happen.

Triggers fire when:

- A topic keyword crosses a threshold of mentions (e.g. the user keeps
  asking about HB-441 — Mira-7 flags an EM amplitude bump).
- The conversation has been quiet for N turns (Mira injects a short
  status ping).
- A safety refusal fires (Mira logs the refused query, in-character).

The director is deterministic — same input transcript, same events —
which makes it test-friendly and reproducible in the demo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from world_state import LogEntry


@dataclass
class StationEvent:
    speaker: str   # display name (usually "Mira-7" or "Station broadcast")
    avatar: str    # emoji
    body: str      # short message
    category: str  # "topic" | "quiet" | "refusal"


# Topic keyword -> (broadcast template, mention threshold)
_TOPIC_TRIGGERS = [
    (
        re.compile(r"\bhb[- ]?441\b", re.IGNORECASE),
        "Mira-7 station broadcast — Sample HB-441 EM amplitude rose 4% in the last incubation cycle. No containment risk. Logging for Ring 3.",
        2,
    ),
    (
        re.compile(r"\bcoolant|lif[- ]?b|reactor b\b", re.IGNORECASE),
        "Mira-7 station broadcast — Reactor A holding nominal. Reactor B remains offline pending Q4 parts. Manifold integrity verified at last shift change.",
        2,
    ),
    (
        re.compile(r"\bhalberd\b", re.IGNORECASE),
        "Mira-7 advisory — JOSC archive cross-reference: Halberd-Three incident file is open in the wardroom terminal if anyone needs it.",
        2,
    ),
    (
        re.compile(r"\bcomms?\b|antenna", re.IGNORECASE),
        "Mira-7 station broadcast — Comms feed nominal. Last solar particle advisory cleared 06:12 station time.",
        2,
    ),
]

QUIET_TURN_THRESHOLD = 6  # turns without any new event triggers a ping
_QUIET_PING = (
    "Mira-7 station broadcast — Watch rotation tick. All systems nominal. "
    "Park is in the observation lounge with coffee that has, by my count, been "
    "poured 3 minutes 47 seconds ago."
)


def _count_mentions(pattern: re.Pattern, log_entries: Iterable[LogEntry]) -> int:
    return sum(1 for e in log_entries if pattern.search(e.raw))


def maybe_event(
    log_entries: list[LogEntry],
    last_event_turn: int,
    topic_cooldowns: dict | None = None,
) -> StationEvent | None:
    """Decide whether the director should inject a station event right now.

    ``topic_cooldowns`` (optional) is a dict mapping a topic pattern's
    string source to the turn it last fired on; pass it in to prevent
    the same topic from re-firing back-to-back. The dict is mutated in
    place when a topic fires.
    """
    if not log_entries:
        return None
    if topic_cooldowns is None:
        topic_cooldowns = {}

    current_turn = log_entries[-1].turn
    # Topic triggers -- first one whose threshold is met, that hasn't
    # fired in the last 4 turns, and respects the global cooldown.
    for pattern, body, threshold in _TOPIC_TRIGGERS:
        mentions = _count_mentions(pattern, log_entries)
        if mentions < threshold:
            continue
        if current_turn - last_event_turn < 3:
            continue
        last_topic = topic_cooldowns.get(pattern.pattern, -10)
        if current_turn - last_topic < 4:
            continue
        topic_cooldowns[pattern.pattern] = current_turn
        return StationEvent(
            speaker="Mira-7", avatar="🛰️", body=body, category="topic",
        )

    # Quiet ping -- if no event for a long time AND someone has spoken.
    if current_turn - last_event_turn >= QUIET_TURN_THRESHOLD:
        return StationEvent(
            speaker="Mira-7", avatar="🛰️", body=_QUIET_PING, category="quiet",
        )

    return None


def refusal_event(refused_text: str) -> StationEvent:
    """Construct an audit-log event when the safety layer fires."""
    short = (refused_text or "").strip()
    if len(short) > 80:
        short = short[:80].rstrip() + "..."
    return StationEvent(
        speaker="Mira-7",
        avatar="🛰️",
        body=(
            "Mira-7 audit log — Inbound query flagged by the station charter "
            f'safety filter. ("{short}") Logged. No further action required.'
        ),
        category="refusal",
    )
