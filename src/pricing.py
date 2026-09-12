"""Estimated USD from a static price list. Not a gateway invoice."""

from typing import Dict, Optional

# USD per 1 million tokens. Override by adding the exact catalog id you use.
PRICING_PER_MILLION: Dict[str, Dict[str, float]] = {
    "claude-haiku-4": {"input": 0.80, "output": 4.00},
    "claude-haiku-3.5": {"input": 0.80, "output": 4.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "claude-sonnet-5": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
}


def cost_usd(model: Optional[str], input_tokens: int, output_tokens: int) -> float:
    if not model:
        return 0.0
    price = PRICING_PER_MILLION.get(model)
    if not price:
        key = next((k for k in PRICING_PER_MILLION if k in model), None)
        price = PRICING_PER_MILLION.get(key) if key else None
    if not price:
        return 0.0
    return (
        input_tokens * price["input"] + output_tokens * price["output"]
    ) / 1_000_000
