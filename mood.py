"""Per-character emotional state.

Each character has a 3-axis mood vector:

  - energy:    1.0 = fresh, 0.0 = tired
  - focus:     1.0 = calm, 0.0 = stressed
  - openness:  1.0 = chatty, 0.0 = curt

Mood shifts in response to:

  - turn count (everyone tires)
  - topic (HB-441 stresses Okafor; coolant stresses Volkov; politics
    tires Park; injuries tire Hua)
  - safety refusals (everyone tightens up a notch)

The mood vector renders into the prompt as a one-line "CURRENT MOOD"
hint and is also used by the offline mock LLM to subtly bias opener
choice (stressed → curt openers).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict


# Per-topic stress multipliers, by character. Negative = stress (drop focus),
# positive = energise. Applied per matching mention.
_TOPIC_EFFECTS = {
    "park": [
        (re.compile(r"\bhalberd\b", re.I), {"focus": -0.05}),
        (re.compile(r"\bjailbreak|hijack\b", re.I), {"focus": -0.10}),
        (re.compile(r"\bcoffee\b", re.I), {"energy": +0.05, "openness": +0.05}),
    ],
    "okafor": [
        (re.compile(r"\bhb[- ]?441\b", re.I), {"energy": +0.10, "focus": -0.05}),
        (re.compile(r"\bdiscover|breakthrough\b", re.I), {"energy": +0.05}),
    ],
    "mira": [
        # Mira is steady; she barely moves.
        (re.compile(r"\bcoolant|reactor\b", re.I), {"focus": -0.02}),
    ],
    "volkov": [
        (re.compile(r"\blif[- ]?b|coolant|leak|reactor b\b", re.I), {"focus": -0.08, "openness": -0.04}),
        (re.compile(r"\bmira\b", re.I), {"openness": -0.03}),
        (re.compile(r"\bvodka|tools\b", re.I), {"openness": +0.05}),
    ],
    "hua": [
        (re.compile(r"\bhb[- ]?441|okafor\b", re.I), {"focus": -0.06}),
        (re.compile(r"\binjur|medical|sick\b", re.I), {"energy": -0.05, "focus": -0.04}),
    ],
}

# How much each turn naturally erodes things (turn 1 → turn 30 difference).
_TURN_DECAY = {"energy": -0.005, "openness": -0.003}


@dataclass
class Mood:
    energy: float = 1.0
    focus: float = 1.0
    openness: float = 1.0

    def clamp(self) -> None:
        self.energy = max(0.0, min(1.0, self.energy))
        self.focus = max(0.0, min(1.0, self.focus))
        self.openness = max(0.0, min(1.0, self.openness))

    def label(self) -> str:
        """Short adjective summary like 'focused, mildly tired'."""
        bits = []
        if self.energy < 0.4:
            bits.append("tired")
        elif self.energy > 0.85:
            bits.append("fresh")
        if self.focus < 0.4:
            bits.append("stressed")
        elif self.focus > 0.85:
            bits.append("calm")
        if self.openness < 0.4:
            bits.append("curt")
        elif self.openness > 0.85:
            bits.append("chatty")
        return ", ".join(bits) if bits else "steady"


@dataclass
class MoodState:
    """Container for all character moods. Lives in session state."""

    moods: Dict[str, Mood] = field(default_factory=dict)
    turns_observed: int = 0
    history: Dict[str, list] = field(default_factory=dict)

    def get(self, character_key: str) -> Mood:
        if character_key not in self.moods:
            self.moods[character_key] = Mood()
        return self.moods[character_key]

    def observe(self, character_key: str, text: str, is_refusal: bool = False) -> Mood:
        """Update mood for `character_key` based on the user input + counters."""
        mood = self.get(character_key)
        self.turns_observed += 1
        # Topic effects
        for pattern, delta in _TOPIC_EFFECTS.get(character_key, []):
            if pattern.search(text or ""):
                for attr, d in delta.items():
                    setattr(mood, attr, getattr(mood, attr) + d)
        # Turn decay
        for attr, d in _TURN_DECAY.items():
            setattr(mood, attr, getattr(mood, attr) + d)
        # Refusals tighten everyone up
        if is_refusal:
            mood.focus -= 0.05
            mood.openness -= 0.05
        mood.clamp()
        # Snapshot for plotting
        snap = {
            "turn": self.turns_observed,
            "energy": mood.energy,
            "focus": mood.focus,
            "openness": mood.openness,
        }
        self.history.setdefault(character_key, []).append(snap)
        # Cap history so it doesn't grow without bound in long sessions.
        if len(self.history[character_key]) > 200:
            self.history[character_key] = self.history[character_key][-200:]
        return mood

    def render_for_prompt(self, character_key: str) -> str:
        mood = self.get(character_key)
        return (
            f"CURRENT MOOD: {mood.label()} "
            f"(energy {mood.energy:.2f}, focus {mood.focus:.2f}, openness {mood.openness:.2f}). "
            "Let it colour your tone subtly — do not announce it."
        )

    def reset(self) -> None:
        self.moods.clear()
        self.turns_observed = 0

    def to_dict(self) -> dict:
        return {
            "turns_observed": self.turns_observed,
            "moods": {k: vars(v) for k, v in self.moods.items()},
        }


def style_bias_from_mood(mood: Mood) -> dict:
    """Hints the mock LLM can use to bias opener/closer choice."""
    return {
        "prefer_short": mood.focus < 0.5 or mood.openness < 0.5,
        "prefer_warm": mood.openness > 0.75,
    }
