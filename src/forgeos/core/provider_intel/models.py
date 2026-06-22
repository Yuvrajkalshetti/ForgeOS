"""Provider Intelligence models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProviderStat(BaseModel):
    """Accumulated raw stats for a (provider, model), persisted and updated."""

    provider: str
    model: str
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    est_cost: float = 0.0
    sum_latency_ms: float = 0.0
    successes: int = 0
    errors: int = 0
    error_breakdown: dict[str, int] = Field(default_factory=dict)
    latency_samples: list[float] = Field(default_factory=list)
    last_seen_at: str = ""
    capabilities: dict[str, Any] = Field(default_factory=dict)


class ProviderScorecard(BaseModel):
    """Computed, human-readable view of a provider/model's behavior."""

    provider: str
    model: str
    calls: int
    tokens_in: int
    tokens_out: int
    est_cost: float
    avg_latency_ms: float
    p95_latency_ms: float
    success_rate: float
    error_breakdown: dict[str, int] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Why a provider was selected and why alternatives were rejected."""

    selected: str
    policy: str
    reason: str
    rejected: list[dict[str, str]] = Field(default_factory=list)
