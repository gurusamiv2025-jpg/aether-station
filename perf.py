"""Performance metrics.

A tiny context-manager timer plus per-operation min/max/avg tracking.
Used to instrument retrieval and LLM calls so the sidebar can show
"retrieval p95: 14ms / LLM p95: 220ms" in real time.

No external dependencies; we use ``time.perf_counter()``.
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Timings:
    samples: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    cap_per_label: int = 200

    def record(self, label: str, ms: float) -> None:
        bucket = self.samples[label]
        bucket.append(ms)
        if len(bucket) > self.cap_per_label:
            bucket.pop(0)

    def stats(self, label: str) -> dict:
        bucket = self.samples.get(label) or []
        if not bucket:
            return {"label": label, "count": 0, "min": 0.0, "avg": 0.0, "max": 0.0, "p95": 0.0}
        n = len(bucket)
        avg = sum(bucket) / n
        sorted_bucket = sorted(bucket)
        p95_idx = max(0, int(0.95 * (n - 1)))
        return {
            "label": label,
            "count": n,
            "min": min(bucket),
            "avg": avg,
            "max": max(bucket),
            "p95": sorted_bucket[p95_idx],
        }

    def all_labels(self) -> List[str]:
        return sorted(self.samples.keys())

    def render(self) -> str:
        if not self.samples:
            return "_(no measurements yet)_"
        lines = ["| operation | n | min | avg | p95 | max |", "|---|---|---|---|---|---|"]
        for label in self.all_labels():
            s = self.stats(label)
            lines.append(
                f"| `{s['label']}` | {s['count']} | {s['min']:.1f}ms | "
                f"{s['avg']:.1f}ms | {s['p95']:.1f}ms | {s['max']:.1f}ms |"
            )
        return "\n".join(lines)


@contextmanager
def timer(timings: Timings, label: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        ms = (time.perf_counter() - start) * 1000.0
        timings.record(label, ms)
