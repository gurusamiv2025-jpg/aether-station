"""In-session analytics for the chatbot.

Tracks lightweight metrics over the lifetime of a Streamlit session:

- queries per character
- top-cited lore files (with average retrieval score)
- safety refusals by category
- average retrieval relevance per character

This is shown as a metrics panel in the UI and helps judges see that the
project tracks its own behavior rather than running blind.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from statistics import mean
from typing import Iterable


@dataclass
class Metrics:
    queries_by_character: Counter = field(default_factory=Counter)
    citations: Counter = field(default_factory=Counter)
    citation_scores: dict = field(default_factory=lambda: defaultdict(list))
    refusals_by_category: Counter = field(default_factory=Counter)
    score_by_character: dict = field(default_factory=lambda: defaultdict(list))
    slash_by_command: Counter = field(default_factory=Counter)
    crises_observed: int = 0
    memos_recorded: int = 0
    handovers_suggested: int = 0
    tools_invoked: Counter = field(default_factory=Counter)

    # --- new counter methods ------------------------------------------
    def record_slash(self, command: str) -> None:
        self.slash_by_command[command] += 1

    def record_crisis(self) -> None:
        self.crises_observed += 1

    def record_memo(self) -> None:
        self.memos_recorded += 1

    def record_handover(self) -> None:
        self.handovers_suggested += 1

    def record_tool(self, tool: str) -> None:
        self.tools_invoked[tool] += 1

    def record_turn(self, character_key: str, turn: dict) -> None:
        self.queries_by_character[character_key] += 1
        if turn.get("refused"):
            cat = "unknown"
            trace = turn.get("trace") or []
            for step in trace:
                if step.get("label") == "Safety layer":
                    # Detail looks like "Input flagged as `jailbreak` — ..."
                    detail = step.get("detail", "")
                    if "`" in detail:
                        cat = detail.split("`")[1]
                    break
            self.refusals_by_category[cat] += 1
            return
        sources = turn.get("sources") or []
        scores = []
        for s in sources:
            self.citations[s["source"]] += 1
            score = float(s.get("score") or 0.0)
            self.citation_scores[s["source"]].append(score)
            scores.append(score)
        if scores:
            self.score_by_character[character_key].append(mean(scores))

    def total_queries(self) -> int:
        return sum(self.queries_by_character.values())

    def total_refusals(self) -> int:
        return sum(self.refusals_by_category.values())

    def top_citations(self, n: int = 5) -> list[tuple[str, int, float]]:
        """Return (source, count, avg_score) sorted by citation count."""
        out = []
        for src, count in self.citations.most_common(n):
            scores = self.citation_scores.get(src) or [0.0]
            out.append((src, count, mean(scores)))
        return out

    def avg_score_for(self, character_key: str) -> float:
        scores = self.score_by_character.get(character_key) or []
        return mean(scores) if scores else 0.0


def render_metrics_text(m: Metrics, character_lookup) -> str:
    """Return a compact markdown summary suitable for the sidebar."""
    lines = [
        f"**Total queries:** {m.total_queries()}  ",
        f"**Refusals:** {m.total_refusals()}",
    ]
    if m.queries_by_character:
        lines.append("\n**Queries by character:**")
        for ch_key, count in m.queries_by_character.most_common():
            ch = character_lookup(ch_key)
            avg = m.avg_score_for(ch_key)
            score_str = f" · avg score {avg:.2f}" if avg else ""
            lines.append(f"- {ch.avatar} {ch.name}: {count}{score_str}")
    top = m.top_citations(5)
    if top:
        lines.append("\n**Most-cited lore:**")
        for src, count, avg in top:
            short = src.replace("lore/", "")
            lines.append(f"- `{short}` — {count}× (avg {avg:.2f})")
    if m.refusals_by_category:
        lines.append("\n**Safety refusals by category:**")
        for cat, count in m.refusals_by_category.most_common():
            lines.append(f"- `{cat}`: {count}")
    if m.slash_by_command:
        lines.append("\n**Slash commands used:**")
        for cmd, count in m.slash_by_command.most_common():
            lines.append(f"- `{cmd}`: {count}")
    if m.tools_invoked:
        lines.append("\n**Tools invoked:**")
        for tool, count in m.tools_invoked.most_common():
            lines.append(f"- `{tool}`: {count}")
    extras = []
    if m.crises_observed:
        extras.append(f"crises observed: {m.crises_observed}")
    if m.memos_recorded:
        extras.append(f"memos recorded: {m.memos_recorded}")
    if m.handovers_suggested:
        extras.append(f"handovers suggested: {m.handovers_suggested}")
    if extras:
        lines.append("\n**Other:** " + ", ".join(extras))
    return "\n".join(lines)
