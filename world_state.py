"""Shared crew memory — the station log.

Every character knows what other crew members have recently said. This is
what makes the cast feel like a crew on the same station rather than five
isolated chatbots: if Volkov just complained about Mira-7's 11-second
delay, Park can reference it when you talk to her two minutes later.

The log lives in Streamlit session state and is also serializable for the
MCP server (so GitHub Copilot can read recent chatter as a tool).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List


# Hard cap on log size, including any summary rollups. The summarizer
# fires before this is reached so context is compressed rather than dropped.
MAX_LOG_ENTRIES = 20
INJECT_PER_PROMPT = 3  # how many to inject into a character's prompt
# When non-summary entries grow past SUMMARY_TRIGGER, the oldest get
# compressed into one "Earlier in this session" rollup, keeping the
# most recent SUMMARY_KEEP_RECENT entries verbatim.
SUMMARY_TRIGGER = 10
SUMMARY_KEEP_RECENT = 6


@dataclass
class LogEntry:
    turn: int
    character: str  # character key (e.g. "park"), "user", or "_summary"
    speaker: str  # display name
    summary: str  # one-sentence summary (~140 chars max)
    raw: str = ""  # original text, kept for the MCP server / debugging
    is_summary: bool = False  # set on compressed "earlier in this session" rollups


@dataclass
class StationLog:
    entries: List[LogEntry] = field(default_factory=list)
    _next_turn: int = 0

    def add(self, character: str, speaker: str, raw: str) -> LogEntry:
        summary = _summarize(raw)
        entry = LogEntry(
            turn=self._next_turn,
            character=character,
            speaker=speaker,
            summary=summary,
            raw=raw,
        )
        self._next_turn += 1
        self.entries.append(entry)
        # First, try compression; only hard-trim as a last resort so we
        # never silently drop context. When we DO hard-trim, preserve
        # any summary rollups since they carry the compressed history.
        self.summarize_if_long()
        if len(self.entries) > MAX_LOG_ENTRIES:
            summaries = [e for e in self.entries if e.is_summary]
            non_summary = [e for e in self.entries if not e.is_summary]
            keep_n = max(MAX_LOG_ENTRIES - len(summaries), 1)
            self.entries = summaries + non_summary[-keep_n:]
        return entry

    def summarize_if_long(self) -> bool:
        """Compress old entries into one rollup when the log grows large.

        Returns True if a summary was created. Idempotent: calling twice
        in a row without new turns does nothing.
        """
        # Find non-summary entries; we never re-summarise existing summaries.
        non_summary = [e for e in self.entries if not e.is_summary]
        if len(non_summary) <= SUMMARY_TRIGGER:
            return False
        if len(non_summary) <= SUMMARY_KEEP_RECENT:
            return False
        cutoff = len(non_summary) - SUMMARY_KEEP_RECENT
        to_compress = non_summary[:cutoff]
        keep = non_summary[cutoff:]
        text_bits = []
        speakers: set[str] = set()
        for e in to_compress:
            speakers.add(e.speaker)
            text_bits.append(f"{e.speaker}: {e.summary}")
        body = " | ".join(text_bits)
        if len(body) > 360:
            body = body[:360].rstrip() + "..."
        rollup = LogEntry(
            turn=to_compress[0].turn,
            character="_summary",
            speaker="Earlier in this session",
            summary=f"({len(to_compress)} turns, speakers: {', '.join(sorted(speakers))}) {body}",
            raw="",
            is_summary=True,
        )
        # Merge into the previous rollup if there already is one — we
        # want at most one "Earlier in this session" entry, not a stack
        # of them.
        existing_summaries = [e for e in self.entries if e.is_summary]
        if existing_summaries:
            prior = existing_summaries[0]
            combined = f"{prior.summary} | {rollup.summary}"
            if len(combined) > 720:
                combined = combined[:720].rstrip() + "..."
            merged = LogEntry(
                turn=prior.turn,
                character="_summary",
                speaker="Earlier in this session",
                summary=combined,
                raw="",
                is_summary=True,
            )
            self.entries = [merged] + keep
        else:
            self.entries = [rollup] + keep
        return True

    def recent(self, n: int = INJECT_PER_PROMPT, exclude_character: str = "") -> List[LogEntry]:
        """Most recent log entries, optionally excluding one character."""
        items = [e for e in self.entries if e.character != exclude_character]
        return items[-n:]

    def to_dict(self) -> list[dict]:
        return [asdict(e) for e in self.entries]


def _summarize(text: str, max_chars: int = 140) -> str:
    """Trivial summarizer: first sentence, truncated."""
    text = text.strip().replace("\n", " ")
    # Take up to the first sentence boundary.
    for end in (". ", "! ", "? "):
        if end in text:
            head = text.split(end, 1)[0] + end[0]
            if len(head) <= max_chars:
                return head
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def format_for_prompt(entries: List[LogEntry]) -> str:
    """Render recent log entries into the system prompt."""
    if not entries:
        return "STATION LOG (recent): (none — quiet shift)"
    lines = ["STATION LOG (recent — what other crew just said):"]
    for e in entries:
        lines.append(f"- T{e.turn} · {e.speaker}: {e.summary}")
    return "\n".join(lines)
