"""Conversation export and import.

Two formats:

- **Markdown** — human-readable transcript for sharing in PRs, emails, or
  Discord. Includes the safety / reasoning / grounding metadata as
  collapsible blockquotes so reviewers see everything in one scroll.

- **JSON** — round-trippable. Save a session, share it with a teammate,
  re-import to continue.

Both formats include schema_version so future-you knows what they are
looking at.
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any

SCHEMA_VERSION = 1


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def to_json(
    histories: dict[str, list[dict]],
    round_table_history: list[dict],
    station_log_entries: list[Any],
) -> str:
    """Serialize a session to JSON string."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "exported_at": _now_iso(),
        "histories": histories,
        "round_table_history": round_table_history,
        "station_log": [
            {
                "turn": e.turn,
                "character": e.character,
                "speaker": e.speaker,
                "summary": e.summary,
                "raw": e.raw,
            }
            for e in station_log_entries
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def from_json(data: str) -> dict:
    """Parse a JSON export. Returns the payload dict."""
    payload = json.loads(data)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported schema_version: {payload.get('schema_version')!r}"
        )
    return payload


def _format_turn_md(turn: dict, character_lookup) -> str:
    if turn["role"] == "user":
        return f"**You:** {turn['content']}\n"
    ch = character_lookup(turn["character"])
    lines = [f"**{ch.name}** ({ch.role}): {turn['content']}", ""]
    if turn.get("refused"):
        lines.append("> _Safety layer refused this input; character stayed in voice._")
        lines.append("")
    sources = turn.get("sources") or []
    if sources:
        lines.append("> _Grounding:_")
        for s in sources:
            lines.append(f"> - `{s['source']}` (score {s['score']:.2f})")
        lines.append("")
    trace = turn.get("trace") or []
    if trace:
        lines.append("<details><summary>Reasoning trace</summary>")
        lines.append("")
        for step in trace:
            lines.append(f"- **{step['label']}** — {step['detail']}")
            for it in step["items"][:5]:
                lines.append(f"  - {it}")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines)


def to_markdown(
    histories: dict[str, list[dict]],
    round_table_history: list[dict],
    character_lookup,
) -> str:
    """Render a Markdown transcript.

    `character_lookup(key)` should return a Character with .name and .role.
    """
    out = [
        "# Aether Station — conversation transcript",
        f"_Exported {_now_iso()}_",
        "",
    ]
    any_content = False
    for ch_key, turns in histories.items():
        if not turns:
            continue
        any_content = True
        ch = character_lookup(ch_key)
        out.append(f"## {ch.name} — {ch.role}")
        out.append("")
        for t in turns:
            out.append(_format_turn_md(t, character_lookup))
        out.append("")
    if round_table_history:
        any_content = True
        out.append("## Round Table")
        out.append("")
        for t in round_table_history:
            out.append(_format_turn_md(t, character_lookup))
    if not any_content:
        out.append("_(no conversation yet — try a scenario from the sidebar)_")
    return "\n".join(out)


def apply_to_state(payload: dict, station_log_cls):
    """Reconstruct session pieces from a payload returned by ``from_json``.

    Returns a dict suitable for slotting back into Streamlit session_state:
    ``{"histories": {...}, "round_table_history": [...], "station_log": <StationLog>}``.

    ``station_log_cls`` is the StationLog class (passed in to avoid an
    import cycle with world_state).
    """
    log = station_log_cls()
    for entry in payload.get("station_log", []):
        log.add(
            character=entry.get("character", "user"),
            speaker=entry.get("speaker", "User"),
            raw=entry.get("raw") or entry.get("summary", ""),
        )
    return {
        "histories": payload.get("histories", {}),
        "round_table_history": payload.get("round_table_history", []),
        "station_log": log,
    }
