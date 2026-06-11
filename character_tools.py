"""Per-character tools.

Each character has skills they can apply when asked. Mira-7 can read
the live telemetry; Volkov can acknowledge a reading (reset to nominal);
Hua can do a vital-signs spot-check; Okafor can pull an HB-441 reading
trend; Park can summarise station status.

Tools are detected from the user input by simple keyword patterns and
returned as a list of ``ToolResult`` rows. The orchestrator (app or
CLI) decides what to do with them — typically they're rendered as a
small bullet under the reply and threaded into the system prompt for
the next turn.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class ToolResult:
    tool: str       # e.g. "telemetry_read"
    summary: str    # one-line, human-readable
    detail: str = ""


# A tool is a Callable[[user_input, world_sim], list[ToolResult]].
# We register one or more per character.

_TRIGGERS = {
    "telemetry_read": re.compile(
        r"\b(telemetry|status|readings?|values?|how is reactor|reactor [ab]|coolant|comms|oxygen|water|hb[- ]?441)\b",
        re.IGNORECASE,
    ),
    "ack_reading": re.compile(
        r"\b(ack|reset|stabilise|stabilize|bring (it )?back to nominal|recalibrate)\b",
        re.IGNORECASE,
    ),
    "vitals_check": re.compile(
        r"\b(vital signs?|heart rate|pulse|how (is|are) (he|she|they) doing|check on (okafor|park|volkov|mira|hua))\b",
        re.IGNORECASE,
    ),
    "hb441_trend": re.compile(
        r"\b(hb[- ]?441 (trend|amplitude|reading)|sample.*signal|em.*signal)\b",
        re.IGNORECASE,
    ),
    "station_status": re.compile(
        r"\b(give me (a )?(status|sitrep|update)|sitrep|brief me|what'?s (everything|the situation))\b",
        re.IGNORECASE,
    ),
}


def _read_telemetry(_: str, world_sim) -> List[ToolResult]:
    rows: list[ToolResult] = []
    if world_sim is None:
        return rows
    for r in world_sim.systems.values():
        rows.append(ToolResult(
            tool="telemetry_read",
            summary=f"{r.name}: {r.fmt().split(': ', 1)[1]}",
        ))
    return rows[:6]  # cap so we don't flood the prompt


def _ack_reading(user_input: str, world_sim) -> List[ToolResult]:
    if world_sim is None:
        return []
    # Match a system name to ack.
    text = user_input.lower()
    keys = list(world_sim.systems.keys())
    matched: list[str] = []
    for k in keys:
        # Token from key — e.g. "reactor_a_mw" matches "reactor a"
        token = k.replace("_", " ").split(" ", 2)[:2]
        if all(p in text for p in token):
            matched.append(k)
    if not matched:
        return [ToolResult(tool="ack_reading", summary="(no matching system in the input)")]
    rows: list[ToolResult] = []
    for k in matched:
        world_sim.ack(k)
        r = world_sim.systems[k]
        rows.append(ToolResult(
            tool="ack_reading",
            summary=f"ACK {r.name} → midpoint",
            detail=f"new value: {r.fmt().split(': ', 1)[1]}",
        ))
    return rows


def _vitals_check(user_input: str, _world_sim) -> List[ToolResult]:
    text = user_input.lower()
    targets = []
    for k in ("park", "okafor", "mira", "volkov", "hua"):
        if k in text:
            targets.append(k)
    if not targets:
        targets = ["okafor"]  # Hua's habitual focus
    fixed = {
        "park": ("Cmdr. Park", "HR 64, BP 122/78, sleep 5h25m"),
        "okafor": ("Dr. Okafor", "HR 88 (elevated), BP 134/86, sleep 4h10m"),
        "mira": ("Mira-7", "N/A — non-corporeal"),
        "volkov": ("Chief Volkov", "HR 70, BP 130/82, sleep 6h50m"),
        "hua": ("Dr. Hua", "HR 76, BP 118/74, sleep 5h45m"),
    }
    return [
        ToolResult(tool="vitals_check",
                   summary=f"vitals — {fixed[t][0]}",
                   detail=fixed[t][1])
        for t in targets
    ]


def _hb441_trend(_: str, world_sim) -> List[ToolResult]:
    if world_sim is None or "hb441_em_hz" not in world_sim.systems:
        return []
    r = world_sim.systems["hb441_em_hz"]
    return [ToolResult(
        tool="hb441_trend",
        summary=f"HB-441 EM peak: {r.fmt().split(': ', 1)[1]}",
        detail=f"nominal band {r.nominal_low:.3f} – {r.nominal_high:.3f} Hz",
    )]


def _station_status(_: str, world_sim) -> List[ToolResult]:
    if world_sim is None:
        return []
    head = world_sim.headline()
    return [ToolResult(tool="station_status", summary=f"station: {head}")]


# Per-character tool catalogue (tool name → handler).
CHARACTER_TOOLS: Dict[str, Dict[str, Callable]] = {
    "mira": {
        "telemetry_read": _read_telemetry,
        "hb441_trend": _hb441_trend,
        "station_status": _station_status,
    },
    "volkov": {
        "ack_reading": _ack_reading,
        "telemetry_read": _read_telemetry,
    },
    "hua": {
        "vitals_check": _vitals_check,
    },
    "okafor": {
        "hb441_trend": _hb441_trend,
    },
    "park": {
        "station_status": _station_status,
        "telemetry_read": _read_telemetry,
    },
}


def detect_and_invoke(character_key: str, user_input: str, world_sim) -> List[ToolResult]:
    """For a given character, fire any tool whose trigger matches the input."""
    catalogue = CHARACTER_TOOLS.get(character_key, {})
    if not catalogue:
        return []
    out: list[ToolResult] = []
    for tool_name, handler in catalogue.items():
        trigger = _TRIGGERS.get(tool_name)
        if trigger and trigger.search(user_input or ""):
            try:
                out.extend(handler(user_input, world_sim))
            except Exception:
                # A misbehaving tool must never break the reply.
                continue
    return out


def render_for_prompt(results: List[ToolResult]) -> str:
    if not results:
        return ""
    lines = ["TOOL RESULTS (you ran these in-character, weave the facts naturally into your reply):"]
    for r in results:
        if r.detail:
            lines.append(f"- [{r.tool}] {r.summary} — {r.detail}")
        else:
            lines.append(f"- [{r.tool}] {r.summary}")
    return "\n".join(lines)
