"""Live station-systems simulation.

The lore bible (markdown) describes the past. This module describes the
*now* — actual numeric values for reactor output, coolant pressure,
oxygen, water, comms link, and crew positions. State advances by one
"tick" per turn, with small stochastic drift.

Characters can be asked "what's Reactor A at?" and answer with a real
number. Mira-7's directorial broadcasts include current readings.

The state is purely in-memory (session-scoped). Reset on Clear.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Dict


@dataclass
class SystemReading:
    name: str
    value: float
    unit: str
    nominal_low: float
    nominal_high: float

    @property
    def status(self) -> str:
        if self.value < self.nominal_low:
            return "below nominal"
        if self.value > self.nominal_high:
            return "above nominal"
        return "nominal"

    def fmt(self) -> str:
        # Pick a sensible precision based on magnitude.
        if abs(self.value) < 1.0:
            number = f"{self.value:.3f}"
        elif abs(self.value) < 100.0:
            number = f"{self.value:.1f}"
        else:
            number = f"{self.value:.0f}"
        return f"{self.name}: {number} {self.unit} ({self.status})"


@dataclass
class StationSim:
    tick: int = 0
    seed: int = 42
    systems: Dict[str, SystemReading] = field(default_factory=dict)
    crew_positions: Dict[str, str] = field(default_factory=dict)
    _rng: random.Random = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        if not self.systems:
            self.systems = {
                "reactor_a_mw": SystemReading("Reactor A output", 9.6, "MW", 8.5, 12.0),
                "reactor_b_mw": SystemReading("Reactor B output", 0.0, "MW", 0.0, 0.0),
                "lif_a_psi": SystemReading("LiF-A loop pressure", 412.0, "psi", 390.0, 430.0),
                "o2_ring1_kpa": SystemReading("Ring 1 oxygen", 21.0, "kPa O2", 19.5, 22.5),
                "o2_ring3_kpa": SystemReading("Ring 3 oxygen", 20.8, "kPa O2", 19.5, 22.5),
                "h2o_reserve_l": SystemReading("Water reserve", 1840.0, "L", 1500.0, 2200.0),
                "comms_db": SystemReading("Comms link margin", 11.4, "dB", 6.0, 14.0),
                "hb441_em_hz": SystemReading("HB-441 EM peak", 0.024, "Hz", 0.018, 0.030),
            }
        if not self.crew_positions:
            self.crew_positions = {
                "park": "command (Ring 1)",
                "okafor": "isolation suite B (Ring 3)",
                "mira": "everywhere",
                "volkov": "engineering hall (Ring 4)",
                "hua": "medbay (Ring 2)",
            }

    # ---- evolution ------------------------------------------------------

    def advance(self, steps: int = 1) -> None:
        """Advance the sim by `steps` ticks, with small stochastic drift."""
        for _ in range(steps):
            self.tick += 1
            # Each reading wobbles within ±0.5% of its nominal midpoint.
            for r in self.systems.values():
                if r.nominal_high == r.nominal_low:
                    continue
                midpoint = (r.nominal_low + r.nominal_high) / 2.0
                drift = self._rng.uniform(-1.0, 1.0) * 0.005 * midpoint
                r.value += drift
                # Small pull-back toward midpoint so we don't wander forever.
                r.value += (midpoint - r.value) * 0.02
            # HB-441 EM signal slowly creeps upward — Okafor's "amplitude bump".
            hb = self.systems.get("hb441_em_hz")
            if hb is not None:
                hb.value += self._rng.uniform(-0.0002, 0.00035)

    def ack(self, key: str) -> None:
        """Acknowledge / reset a reading toward midpoint (engineer action)."""
        if key in self.systems:
            r = self.systems[key]
            r.value = (r.nominal_low + r.nominal_high) / 2.0

    # ---- prompt rendering ----------------------------------------------

    def render_for_prompt(self) -> str:
        lines = ["LIVE STATION TELEMETRY (current):"]
        for r in self.systems.values():
            lines.append(f"- {r.fmt()}")
        lines.append("CREW POSITIONS:")
        for k, where in self.crew_positions.items():
            lines.append(f"- {k}: {where}")
        return "\n".join(lines)

    def headline(self) -> str:
        """Single-sentence summary used by the director."""
        alarms = [r for r in self.systems.values() if r.status != "nominal" and r.nominal_high != r.nominal_low]
        if alarms:
            return "; ".join(r.fmt() for r in alarms[:3])
        return f"All monitored systems nominal at tick {self.tick}."

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "seed": self.seed,
            "systems": {k: asdict(v) for k, v in self.systems.items()},
            "crew_positions": dict(self.crew_positions),
        }
