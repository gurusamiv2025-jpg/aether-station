"""Character handover — suggest the right specialist.

When the user asks the active character something outside their lane,
the active character should offer to hand over to whoever's actually
qualified. Volkov shouldn't lecture on cell biology; Okafor shouldn't
explain torque values. Each character knows their expertise + the
referrals they'd make.

The detector is intentionally simple: regex topic matching against a
catalogue. The output is a HandoverSuggestion which the prompt layer
weaves in as a short instruction ("You can answer briefly but recommend
the user ask Okafor for depth.").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class HandoverSuggestion:
    speaker: str         # current character (who would defer)
    refer_to: str        # who they would defer TO
    topic: str           # short label of the topic that triggered it

    def to_prompt(self) -> str:
        return (
            f"HANDOVER HINT: this question touches {self.topic}, which is really "
            f"the '{self.refer_to}' role's domain. Answer briefly from your own "
            f"perspective and explicitly suggest the user follow up with them."
        )


# (topic_label, regex) -> primary specialist key
_TOPIC_SPECIALISTS: list[tuple[str, str, re.Pattern]] = [
    ("xenobiology / HB-441 specifics",       "okafor", re.compile(r"\bhb[- ]?441 (signal|sample|biology|amplitude)\b|\bbiofilm\b|\bxenobiol", re.IGNORECASE)),
    ("reactor / coolant / engineering",      "volkov", re.compile(r"\breactor [ab]\b|\blif[- ]?[ab]\b|\bcoolant\b|\btorque\b|\bweld\b|\bmanifold\b", re.IGNORECASE)),
    ("crew medical / vitals",                "hua",    re.compile(r"\bvital signs?\b|\bheart rate\b|\bpulse\b|\bmedical\b|\binjur", re.IGNORECASE)),
    ("station ai / comms / telemetry",       "mira",   re.compile(r"\bcomms?\b|\btelemetry\b|\bsensor\b|\bbroadcast\b|\bstation ai\b", re.IGNORECASE)),
    ("command / policy / JOSC charter",      "park",   re.compile(r"\bcommander\b|\bcharter\b|\bJOSC\b|\bcommand decision\b|\bauthority\b|\boverride\b", re.IGNORECASE)),
]


# Things a character should never defer on (their own dossier and self).
_NEVER_REDIRECT_SELF = True


def detect(speaker_key: str, user_input: str) -> Optional[HandoverSuggestion]:
    """If the question lands outside the speaker's lane, return a suggestion."""
    if not user_input:
        return None
    for topic, specialist, rx in _TOPIC_SPECIALISTS:
        if rx.search(user_input) and specialist != speaker_key:
            return HandoverSuggestion(
                speaker=speaker_key,
                refer_to=specialist,
                topic=topic,
            )
    return None


def render_for_prompt(suggestion: Optional[HandoverSuggestion]) -> str:
    if suggestion is None:
        return ""
    return suggestion.to_prompt()
