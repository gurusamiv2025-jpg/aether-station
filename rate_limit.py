"""Per-IP token-bucket rate limiter.

The HTTP API exposes endpoints that, in a hosted deployment, an
adversary could pelt with prompt-injection attempts to burn LLM
budget. A small in-process token bucket keeps that under control: each
client IP gets ``BUCKET_SIZE`` tokens that refill at ``REFILL_PER_SEC``
tokens/second; a request costs one token.

This is in-process state — fine for a single uvicorn worker, not for a
multi-process / multi-replica deployment. For production you'd hand
this off to Redis or your reverse proxy.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


DEFAULT_BUCKET_SIZE = 30        # burst capacity
DEFAULT_REFILL_PER_SEC = 0.5    # 30 tokens/min sustained


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


@dataclass
class RateLimiter:
    bucket_size: float = DEFAULT_BUCKET_SIZE
    refill_per_sec: float = DEFAULT_REFILL_PER_SEC
    buckets: Dict[str, _Bucket] = field(default_factory=dict)

    def check(self, client_id: str, cost: float = 1.0) -> bool:
        """Consume `cost` tokens for `client_id`. Returns True if allowed."""
        now = time.monotonic()
        b = self.buckets.get(client_id)
        if b is None:
            b = _Bucket(tokens=self.bucket_size, last_refill=now)
            self.buckets[client_id] = b
        # Refill.
        elapsed = now - b.last_refill
        if elapsed > 0:
            b.tokens = min(self.bucket_size, b.tokens + elapsed * self.refill_per_sec)
            b.last_refill = now
        if b.tokens >= cost:
            b.tokens -= cost
            return True
        return False

    def remaining(self, client_id: str) -> float:
        b = self.buckets.get(client_id)
        return b.tokens if b is not None else self.bucket_size
