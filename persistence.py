"""Full-state persistence to disk.

Rounds 1–20 kept everything in Streamlit session state — fine for a
live demo, but the world simulation, persona memory, mood history, and
memo book all vanish on browser refresh or container restart. This
module dumps the durable parts of the session to a single JSON file
and reads them back.

The on-disk format is versioned. We never silently load an older or
newer schema — we either succeed cleanly or refuse.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

SCHEMA_VERSION = 1

# Conservative default location — user-overridable through the UI.
DEFAULT_PATH = Path.cwd() / ".aether-session.json"


def _system_to_dict(r) -> Dict[str, Any]:
    return {
        "name": r.name,
        "value": r.value,
        "unit": r.unit,
        "nominal_low": r.nominal_low,
        "nominal_high": r.nominal_high,
    }


def serialize(*, world_sim, persona_memory, mood_state, audit_log, memo_book) -> str:
    """Build the on-disk JSON payload."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "world_sim": {
            "tick": world_sim.tick,
            "seed": world_sim.seed,
            "systems": {k: _system_to_dict(v) for k, v in world_sim.systems.items()},
            "crew_positions": dict(world_sim.crew_positions),
        },
        "persona_memory": persona_memory.to_dict(),
        "mood_state": mood_state.to_dict(),
        "audit_log": [asdict(e) for e in audit_log.entries],
        "memo_book": memo_book.to_dict(),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def write_to(path, *, world_sim, persona_memory, mood_state, audit_log, memo_book) -> Path:
    p = Path(path)
    p.write_text(
        serialize(
            world_sim=world_sim, persona_memory=persona_memory,
            mood_state=mood_state, audit_log=audit_log, memo_book=memo_book,
        ),
        encoding="utf-8",
    )
    return p


def read_from(path) -> dict:
    """Load and validate a session JSON. Raises on schema mismatch."""
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported schema_version: {payload.get('schema_version')!r}"
        )
    return payload


def apply(payload: dict, *, world_sim_cls, persona_memory_cls,
          mood_state_cls, audit_log_cls, memo_book_cls) -> dict:
    """Re-hydrate domain objects from a payload. Returns a dict of new instances."""
    from world_sim import SystemReading

    sim = world_sim_cls()
    sim.tick = int(payload["world_sim"]["tick"])
    sim.seed = int(payload["world_sim"]["seed"])
    sim.systems = {
        k: SystemReading(
            name=v["name"], value=float(v["value"]), unit=v["unit"],
            nominal_low=float(v["nominal_low"]), nominal_high=float(v["nominal_high"]),
        )
        for k, v in payload["world_sim"]["systems"].items()
    }
    sim.crew_positions = dict(payload["world_sim"]["crew_positions"])

    pm = persona_memory_cls.from_dict(payload.get("persona_memory") or {})

    ms = mood_state_cls()
    moods = payload.get("mood_state", {}).get("moods") or {}
    from mood import Mood
    for k, v in moods.items():
        ms.moods[k] = Mood(
            energy=float(v.get("energy", 1.0)),
            focus=float(v.get("focus", 1.0)),
            openness=float(v.get("openness", 1.0)),
        )
    ms.turns_observed = int(payload.get("mood_state", {}).get("turns_observed", 0))

    al = audit_log_cls()
    from audit import AuditEntry
    for row in payload.get("audit_log", []):
        al.entries.append(AuditEntry(
            ts=row["ts"], kind=row["kind"], character=row["character"],
            summary=row["summary"], detail=row.get("detail", ""),
        ))

    mb = memo_book_cls()
    from memo import Memo
    for row in payload.get("memo_book", []):
        mb.entries.append(Memo(
            ts=row["ts"], kind=row["kind"], title=row["title"],
            detail=row.get("detail", ""),
        ))
        mb._seen.add(row["kind"])

    return {
        "world_sim": sim,
        "persona_memory": pm,
        "mood_state": ms,
        "audit_log": al,
        "memo_book": mb,
    }
