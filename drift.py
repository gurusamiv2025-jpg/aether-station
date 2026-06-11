"""Personality drift detector.

Each character has a voice signature — recognizable openers, idioms,
fact-leads, and address forms. If a reply lacks every one of those, the
character is drifting (out of voice). This module scores each reply
against the signature and flags drift to the UI.

The detector is intentionally simple: pattern recognition, not ML. The
goal is to catch obvious regressions like "the LLM forgot we're in
character," not subtle stylistic shifts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class DriftReport:
    character: str
    score: float        # 0.0 = totally adrift, 1.0 = clearly in voice
    signals: List[str]  # which signals matched
    flagged: bool       # score < threshold

    def label(self) -> str:
        if self.score >= 0.5:
            return "in voice"
        if self.score >= 0.25:
            return "weak voice"
        return "drift"


DRIFT_THRESHOLD = 0.25  # below this, we flag the reply
RECENT_REPLIES = 5      # how many turns to roll up when scoring a character


def _signatures_for(character_key: str) -> dict:
    """Pull voice signals out of llm._VOICE_PROFILES + ADDRESS_FORMS."""
    try:
        from llm import _VOICE_PROFILES, ADDRESS_FORMS
    except Exception:
        return {"openers": [], "closers": [], "idioms": [], "fact_lead": "", "addresses": []}
    profile = _VOICE_PROFILES.get(character_key, {})
    addresses = list(ADDRESS_FORMS.get(character_key, {}).values())
    return {
        "openers": list(profile.get("openers", []))
                   + list(profile.get("short_openers", []))
                   + list(profile.get("warm_openers", [])),
        "closers": list(profile.get("closers", [])),
        "idioms": list(profile.get("idioms", [])),
        "fact_lead": profile.get("fact_lead", ""),
        "addresses": addresses,
    }


def score_reply(character_key: str, reply: str) -> DriftReport:
    """Score a single reply. Returns DriftReport."""
    signals: list[str] = []
    if not reply:
        return DriftReport(character=character_key, score=0.0, signals=[], flagged=True)
    sigs = _signatures_for(character_key)
    text = reply
    # Each match contributes a fixed weight; cap at 1.0.
    weight = 0.0
    for o in sigs["openers"]:
        if o in text:
            signals.append(f"opener:{o!r}")
            weight = max(weight, 0.35)
            break
    for c in sigs["closers"]:
        if c in text:
            signals.append(f"closer:{c!r}")
            weight = max(weight, weight + 0.25)
            break
    for i in sigs["idioms"]:
        if i in text:
            signals.append(f"idiom:{i!r}")
            weight = max(weight, weight + 0.20)
            break
    if sigs["fact_lead"] and sigs["fact_lead"] in text:
        signals.append("fact_lead")
        weight = max(weight, weight + 0.15)
    for a in sigs["addresses"]:
        # Whole-word check against the form (e.g. "Kostya", "Doctor")
        if f" {a} " in f" {text} " or text.startswith(a) or text.endswith(a):
            signals.append(f"address:{a!r}")
            weight = max(weight, weight + 0.10)
            break
    score = min(weight, 1.0)
    return DriftReport(
        character=character_key,
        score=score,
        signals=signals,
        flagged=score < DRIFT_THRESHOLD,
    )


def score_recent(character_key: str, replies: Iterable[str]) -> DriftReport:
    """Average drift across the last few replies for one character."""
    replies = list(replies)[-RECENT_REPLIES:]
    if not replies:
        return DriftReport(character=character_key, score=1.0, signals=[], flagged=False)
    reports = [score_reply(character_key, r) for r in replies]
    avg = sum(r.score for r in reports) / len(reports)
    collected: list[str] = []
    for r in reports:
        for s in r.signals:
            if s not in collected:
                collected.append(s)
    return DriftReport(
        character=character_key,
        score=avg,
        signals=collected[:8],
        flagged=avg < DRIFT_THRESHOLD,
    )
