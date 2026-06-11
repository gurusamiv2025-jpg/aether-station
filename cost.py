"""Approximate token + cost estimator.

We can't see real token counts without calling the model, but an
approximation (chars / 4) is close enough to give the user a running
sense of spend. Defaults to **Azure OpenAI gpt-4o-mini** pricing (June
2024 list prices, USD / 1M tokens); override via constructor.

This is a *demo* estimator — for production billing use the actual
``usage.prompt_tokens`` field on the API response.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# gpt-4o-mini list prices (USD per 1M tokens) — current as of submission.
DEFAULT_INPUT_PRICE_PER_M = 0.15
DEFAULT_OUTPUT_PRICE_PER_M = 0.60


def approx_tokens(text: str) -> int:
    """Cheap heuristic: roughly chars/4 + small overhead per call."""
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class CostEstimate:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    input_price_per_m: float = DEFAULT_INPUT_PRICE_PER_M
    output_price_per_m: float = DEFAULT_OUTPUT_PRICE_PER_M

    def record(self, system_prompt: str, user_prompt: str, reply: str) -> None:
        self.input_tokens += approx_tokens(system_prompt) + approx_tokens(user_prompt)
        self.output_tokens += approx_tokens(reply)
        self.calls += 1

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_usd(self) -> float:
        return (
            (self.input_tokens / 1_000_000.0) * self.input_price_per_m
            + (self.output_tokens / 1_000_000.0) * self.output_price_per_m
        )

    def render(self) -> str:
        if self.calls == 0:
            return "_(no LLM calls yet — cost = $0.00)_"
        return (
            f"**LLM calls:** {self.calls}  \n"
            f"**Input tokens (approx.):** {self.input_tokens:,}  \n"
            f"**Output tokens (approx.):** {self.output_tokens:,}  \n"
            f"**Estimated cost:** ${self.estimated_usd:.4f} USD  "
            f"_(gpt-4o-mini list pricing; offline mock = $0)_"
        )
