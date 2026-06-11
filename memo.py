"""Conversation milestone tracker.

Auto-detects notable moments in a session and captures them as memos:
the first character switch, the first safety refusal, the first
persona note, the first dialogue chain, the first crisis the user
encountered. Each is recorded once with a timestamp.

The memos surface as a sidebar timeline so a returning user gets a
"here's what happened" overview without scrolling the chat.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class Memo:
    ts: str       # ISO-8601 UTC
    kind: str     # short identifier (e.g. "first_refusal")
    title: str    # display title
    detail: str = ""


@dataclass
class MemoBook:
    entries: List[Memo] = field(default_factory=list)
    _seen: Set[str] = field(default_factory=set)

    def _now(self) -> str:
        return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")

    def _once(self, kind: str, title: str, detail: str = "") -> bool:
        """Record a memo if we haven't seen its kind before. True if added."""
        if kind in self._seen:
            return False
        self._seen.add(kind)
        self.entries.append(Memo(ts=self._now(), kind=kind, title=title, detail=detail))
        return True

    # --- semantic recorders -------------------------------------------------

    def record_turn(self, character: str, turn: dict) -> List[str]:
        """Inspect a turn and emit any first-time milestones. Returns a list
        of memo kinds added on this call (empty if none).
        """
        added: list[str] = []
        if self._once("first_reply", "First reply received",
                      f"character: {character}"):
            added.append("first_reply")
        if turn.get("refused"):
            if self._once("first_refusal", "First safety refusal",
                          f"character: {character}"):
                added.append("first_refusal")
        if turn.get("memory_event"):
            if self._once("first_note", "First persona note recorded",
                          f"character: {character}"):
                added.append("first_note")
        if turn.get("tool_results"):
            if self._once("first_tool", "First tool invocation",
                          f"character: {character}, tools: " +
                          ", ".join(r['tool'] for r in turn['tool_results'])):
                added.append("first_tool")
        return added

    def record_crisis_first(self, system_name: str) -> bool:
        return self._once("first_crisis", "First active crisis detected",
                          f"system: {system_name}")

    def record_dialogue_first(self, a: str, b: str, topic: str) -> bool:
        return self._once("first_dialogue", "First inter-character dialogue",
                          f"{a} ↔ {b} · topic: {topic}")

    def record_switch(self, prev: str, new: str) -> bool:
        # Only the very first switch is a milestone.
        return self._once("first_switch", "First character switch",
                          f"{prev} → {new}")

    def __len__(self) -> int:
        return len(self.entries)

    def to_markdown(self) -> str:
        if not self.entries:
            return "_(no memos yet)_"
        lines = []
        for m in self.entries:
            extra = f" — {m.detail}" if m.detail else ""
            lines.append(f"- **{m.title}**{extra}  \n  _{m.ts}_")
        return "\n".join(lines)

    def to_dict(self) -> list[dict]:
        return [{"ts": m.ts, "kind": m.kind, "title": m.title, "detail": m.detail}
                for m in self.entries]
