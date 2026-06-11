"""Crisis detector + emergency routing.

When the world simulation drifts out of nominal, this module surfaces
an *emergency context* the character pipeline can inject into the
system prompt. The crisis carries:

- which system tripped
- who the right specialist is
- a short "incident commander" hint the character can lean on

Crises are passive: they don't push notifications. They surface as a
sidebar banner and inject into prompts so the cast reflects the
current state naturally ("Reactor A at 8.1 MW — below nominal — we
should bring B's reserve up.").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# Who owns each system in a crisis. Drives handover hints and the
# Director's escalation routing.
_SYSTEM_OWNERSHIP = {
    "reactor_a_mw": "volkov",
    "reactor_b_mw": "volkov",
    "lif_a_psi":    "volkov",
    "o2_ring1_kpa": "mira",
    "o2_ring3_kpa": "mira",
    "h2o_reserve_l": "volkov",
    "comms_db":     "mira",
    "hb441_em_hz":  "okafor",
}


@dataclass
class CrisisEvent:
    system_key: str       # e.g. "reactor_a_mw"
    system_name: str      # display name, e.g. "Reactor A output"
    value: float
    status: str           # "below nominal" / "above nominal"
    owner_key: str        # character key
    severity: str         # "watch" | "alarm"

    def to_prompt(self) -> str:
        return (
            f"ACTIVE CRISIS: {self.system_name} is {self.status} ({self.value:.2f}). "
            f"The on-duty specialist is the '{self.owner_key}' role. "
            "Reflect this in your reply if and only if the user's question touches it."
        )

    def to_banner(self) -> str:
        return f"⚠ {self.system_name}: {self.status} ({self.value:.2f}) → owner: {self.owner_key}"


def scan(world_sim) -> List[CrisisEvent]:
    """Return one CrisisEvent per system currently out of nominal."""
    events: list[CrisisEvent] = []
    if world_sim is None:
        return events
    for key, r in world_sim.systems.items():
        # Skip systems where high == low (Reactor B is intentionally 0/0).
        if r.nominal_high == r.nominal_low:
            continue
        if r.status == "nominal":
            continue
        # Severity scales with how far out of band we are.
        band = r.nominal_high - r.nominal_low or 1.0
        if r.value < r.nominal_low:
            distance = (r.nominal_low - r.value) / band
        else:
            distance = (r.value - r.nominal_high) / band
        severity = "alarm" if distance > 0.5 else "watch"
        events.append(CrisisEvent(
            system_key=key,
            system_name=r.name,
            value=r.value,
            status=r.status,
            owner_key=_SYSTEM_OWNERSHIP.get(key, "park"),
            severity=severity,
        ))
    return events


def render_for_prompt(events: List[CrisisEvent]) -> str:
    if not events:
        return ""
    lines = ["CRISIS CONTEXT (active station alarms — weave in only if relevant):"]
    for e in events:
        lines.append(f"- {e.to_prompt()}")
    return "\n".join(lines)


def owner(system_key: str) -> str:
    """Public lookup for the owner of a system."""
    return _SYSTEM_OWNERSHIP.get(system_key, "park")
