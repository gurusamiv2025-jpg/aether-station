"""Per-character learned facts within a session.

Each character has a small short-term memory of facts the user told
them. Triggers:

- ``"for the record, X"`` → record X
- ``"make a note: X"`` → record X
- ``"forget the X note"`` → drop matching facts
- ``"clear your notes"`` → drop everything

Facts get injected into the character's system prompt under a
``PERSONAL NOTES`` header so the character can reference them in
future turns. Kept small (cap per character) so the prompt stays lean.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

MAX_FACTS_PER_CHARACTER = 6
MAX_FACT_LENGTH = 180


_RECORD_PATTERNS = [
    re.compile(r"^\s*for the record[,:]?\s*(.+)$", re.IGNORECASE),
    re.compile(r"^\s*make a note[,:]?\s*(.+)$", re.IGNORECASE),
    re.compile(r"^\s*remember (?:that |this[:,] |the following[:,] )?(.+)$", re.IGNORECASE),
    re.compile(r"^\s*note to self[,:]?\s*(.+)$", re.IGNORECASE),
]
_FORGET_ALL = re.compile(r"\b(clear|wipe|forget) (your |all |my )?notes?\b", re.IGNORECASE)
_FORGET_ONE = re.compile(r"\bforget (the |that )?(.+?) note\b", re.IGNORECASE)


@dataclass
class PersonaMemory:
    facts: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    def observe(self, character_key: str, user_input: str) -> dict:
        """Process a user message; possibly record/forget facts.

        Returns ``{"recorded": [...], "forgot": int, "cleared": bool}``
        for UI feedback. Always called *before* sending input to the LLM.
        """
        result = {"recorded": [], "forgot": 0, "cleared": False}
        if not user_input:
            return result

        if _FORGET_ALL.search(user_input):
            removed = len(self.facts.get(character_key, []))
            self.facts[character_key] = []
            result["cleared"] = True
            result["forgot"] = removed
            return result

        m = _FORGET_ONE.search(user_input)
        if m:
            needle = m.group(2).strip().lower()
            current = self.facts.get(character_key, [])
            kept = [f for f in current if needle not in f.lower()]
            result["forgot"] = len(current) - len(kept)
            self.facts[character_key] = kept

        for pat in _RECORD_PATTERNS:
            for m in pat.finditer(user_input):
                fact = m.group(1).strip().rstrip(".!?")
                if not fact:
                    continue
                if len(fact) > MAX_FACT_LENGTH:
                    fact = fact[:MAX_FACT_LENGTH].rstrip() + "..."
                bucket = self.facts.setdefault(character_key, [])
                if fact.lower() in (f.lower() for f in bucket):
                    continue
                bucket.append(fact)
                if len(bucket) > MAX_FACTS_PER_CHARACTER:
                    bucket.pop(0)
                result["recorded"].append(fact)
        return result

    def get(self, character_key: str) -> List[str]:
        return list(self.facts.get(character_key, []))

    def render_for_prompt(self, character_key: str) -> str:
        items = self.get(character_key)
        if not items:
            return "PERSONAL NOTES: (none)"
        body = "\n".join(f"- {f}" for f in items)
        return "PERSONAL NOTES (things this character was told to remember):\n" + body

    def to_dict(self) -> dict:
        return {k: list(v) for k, v in self.facts.items() if v}

    @classmethod
    def from_dict(cls, payload) -> "PersonaMemory":
        pm = cls()
        if isinstance(payload, dict):
            for k, v in payload.items():
                if isinstance(v, list):
                    pm.facts[k] = [str(x) for x in v]
        return pm
