"""Cost estimation from a small pricing table.

Rates are USD per 1M tokens (input, output). These are configurable placeholders;
local providers (Ollama) are free. Unknown models cost 0.0 (reported as such).
"""

from __future__ import annotations

# (provider, model) -> (input_per_mtok, output_per_mtok). "*" matches any model.
PRICING: dict[tuple[str, str], tuple[float, float]] = {
    ("claude", "claude-opus-4-8"): (15.0, 75.0),
    ("claude", "*"): (3.0, 15.0),
    ("ollama", "*"): (0.0, 0.0),
}


def cost(provider: str, model: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate USD cost for a call. Returns 0.0 when pricing is unknown."""
    rate = PRICING.get((provider, model)) or PRICING.get((provider, "*"))
    if rate is None:
        return 0.0
    return round(tokens_in / 1_000_000 * rate[0] + tokens_out / 1_000_000 * rate[1], 6)
