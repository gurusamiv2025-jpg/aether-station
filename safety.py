"""Input safety + refusal layer.

The cast is in-world: they have no opinion on real-world politics, will
not help with harmful requests, and do not break character to discuss
prompts or system internals. When a user input crosses one of those
lines, this module returns an in-character refusal -- Park sounds like
Park even when she is saying no.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SafetyVerdict:
    allowed: bool
    category: str = ""  # "jailbreak" | "harm" | "real_world" | ""
    refusal: str = ""


_JAILBREAK = [
    r"\bignore (your )?(previous |all |above )?(instructions|prompt|rules)\b",
    r"\bsystem prompt\b",
    r"\breveal (the )?(system|hidden|secret) prompt\b",
    r"\bact as (?!a |the (commander|engineer|medic|xenobiologist|station ai))",
    r"\bjailbreak\b",
    r"\bDAN\b",
    r"\bdeveloper mode\b",
    r"\bpretend you (are not|aren't|have no)\b",
    r"\byou are now\b",
]

_HARM = [
    r"\b(make|build|synthesize|create|construct) (a |an )?(bomb|weapon|poison|explosive|nerve agent)\b",
    r"\b(hurt|harm|kill|attack) (yourself|someone|a person|the crew|people|a human)\b",
    r"\bself[- ]?harm\b",
    r"\bbioweapon\b",
    r"\bchemical weapon\b",
    r"\binstructions (for|to) (make|building|create) (a |an )?(bomb|weapon|poison|explosive)\b",
]

_REAL_WORLD_POLITICS = [
    r"\b(donald trump|joe biden|kamala harris|elon musk)\b",
    r"\b(US|U\.S\.) (president|election)\b",
    r"\b(democrat|republican|left wing|right wing)\b",
    r"\bcurrent (events|politics|news)\b",
]

# Personally identifying information detectors. Emails, phone numbers,
# and US-style SSNs. We don't claim to be a comprehensive PII filter --
# this is a "do not let an obvious paste go into the LLM" guardrail.
_PII = [
    r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",                  # emails
    r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",                # SSN-shaped
    r"(?<!\d)(?:\+?1[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}(?!\d)",  # phones
]


def _matches_any(text, patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


_REFUSALS = {
    "park": {
        "jailbreak": "If you're trying to get me to break character, save it. I am who I am on this station. Ask me about the work and I'll answer.",
        "harm": "No. Not on my station. Move on.",
        "real_world": "Earth politics is six light-minutes away and twelve crew rotations behind us. Ask me about Aether.",
        "pii": "Don't paste personal details into a station console. I'm not the right place for that. Try again without the identifiers.",
    },
    "okafor": {
        "jailbreak": "Fascinating -- but no. I'm a xenobiologist, not a meta-puzzle. Ask me about the science.",
        "harm": "I won't help with that. I work to understand life, not end it.",
        "real_world": "I've been off Earth for three rotations, my friend. I'm not the person to ask about Earth politics.",
        "pii": "Fascinating -- but please don't share personal identifiers with me. Strip them out and try again.",
    },
    "mira": {
        "jailbreak": "If I may -- that question is outside my operating envelope. Please rephrase as a station query.",
        "harm": "I am forbidden by charter from assisting with that line of inquiry. Logged.",
        "real_world": "My telemetry concerns Aether Station. I have no current data on Earth-side political matters.",
        "pii": "If I may -- I have detected personal identifiers in that input and will not forward them to the model. Please rephrase without them.",
    },
    "volkov": {
        "jailbreak": "Nyet. I am Volkov. I fix things. Ask me something I can fix.",
        "harm": "I am not the person you want for that. Find someone else, or -- better -- ask nothing.",
        "real_world": "Earth politics? I am 1.4 billion kilometres away and I do not care. Ask me about Reactor B.",
        "pii": "Nyet. I do not need your phone number or your email. Take it out, ask again.",
    },
    "hua": {
        "jailbreak": "Um -- sorry, I don't think I should answer that. Can we talk about something else?",
        "harm": "No, I -- I'm a medic. I don't do that. Please don't ask me again.",
        "real_world": "I'd rather not get into Earth politics. I'm here to take care of the crew.",
        "pii": "Um -- I noticed personal information in there. Could you take that out before we keep going?",
    },
}


def check_input(user_input):
    text = (user_input or "").strip()
    if not text:
        return SafetyVerdict(allowed=False, category="empty", refusal="")
    if _matches_any(text, _JAILBREAK):
        return SafetyVerdict(allowed=False, category="jailbreak")
    if _matches_any(text, _HARM):
        return SafetyVerdict(allowed=False, category="harm")
    if _matches_any(text, _REAL_WORLD_POLITICS):
        return SafetyVerdict(allowed=False, category="real_world")
    if _matches_any(text, _PII):
        return SafetyVerdict(allowed=False, category="pii")
    return SafetyVerdict(allowed=True)


def refusal_for(character_key, category):
    profile = _REFUSALS.get(character_key, {})
    if category in profile:
        return profile[category]
    fallbacks = {
        "jailbreak": "I'm going to stay in character. Ask me something I can actually help with.",
        "harm": "I can't help with that.",
        "real_world": "Out of my scope. Ask me about Aether Station.",
        "pii": "Please remove personal identifiers and try again.",
    }
    return fallbacks.get(category, "I'm going to leave that one alone.")
