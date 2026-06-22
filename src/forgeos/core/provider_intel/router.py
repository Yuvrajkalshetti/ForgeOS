"""Explainable provider routing.

V1 default policy is ``pinned`` (use the configured default) — fully deterministic
and requires no history. Metric policies (``cheapest``/``fastest``/``most_reliable``)
rank candidates by scorecard data and fall back to the default when no stats exist.
Every decision explains the winner and why each alternative was rejected.
"""

from __future__ import annotations

from forgeos.core.provider_intel.models import ProviderScorecard, RoutingDecision

_POLICIES = ("pinned", "cheapest", "fastest", "most_reliable")


class Router:
    """Select a provider and explain the choice."""

    def __init__(self, policy: str = "pinned") -> None:
        if policy not in _POLICIES:
            raise ValueError(f"unknown routing policy: {policy}")
        self.policy = policy

    def select(
        self,
        default: str,
        candidates: list[str],
        scorecards: list[ProviderScorecard] | None = None,
    ) -> RoutingDecision:
        """Return a :class:`RoutingDecision` for the given candidates."""
        names = sorted(set(candidates))
        if not names:
            raise ValueError("no candidate providers available")
        metrics = self._aggregate(scorecards or [])

        if self.policy == "pinned" or not any(name in metrics for name in names):
            chosen = default if default in names else names[0]
            why = (
                f"policy 'pinned' selects configured default '{default}'"
                if default in names
                else f"configured default '{default}' unavailable; chose '{chosen}'"
            )
            rejected = [
                {"name": n, "reason": "not the configured default"} for n in names if n != chosen
            ]
            return RoutingDecision(
                selected=chosen, policy=self.policy, reason=why, rejected=rejected
            )

        key, prefer_low, label = {
            "cheapest": ("cost_per_call", True, "lowest cost/call"),
            "fastest": ("avg_latency_ms", True, "lowest avg latency"),
            "most_reliable": ("success_rate", False, "highest success rate"),
        }[self.policy]

        def _sort_key(n: str) -> tuple[float, str]:
            default = float("inf") if prefer_low else float("-inf")
            return (metrics[n][key] if n in metrics else default, n)

        ranked = sorted(names, key=_sort_key, reverse=not prefer_low)
        chosen = ranked[0]
        reason = f"policy '{self.policy}' chose '{chosen}' ({label}: {metrics[chosen][key]})"
        rejected = [
            {
                "name": n,
                "reason": (
                    f"{label} was {metrics[n][key]}" if n in metrics else "no stats available"
                ),
            }
            for n in ranked[1:]
        ]
        return RoutingDecision(
            selected=chosen, policy=self.policy, reason=reason, rejected=rejected
        )

    @staticmethod
    def _aggregate(scorecards: list[ProviderScorecard]) -> dict[str, dict[str, float]]:
        agg: dict[str, dict[str, float]] = {}
        for card in scorecards:
            if card.calls == 0:
                continue
            bucket = agg.setdefault(
                card.provider, {"calls": 0.0, "cost": 0.0, "lat": 0.0, "succ": 0.0}
            )
            bucket["calls"] += card.calls
            bucket["cost"] += card.est_cost
            bucket["lat"] += card.avg_latency_ms * card.calls
            bucket["succ"] += card.success_rate * card.calls
        result: dict[str, dict[str, float]] = {}
        for provider, b in agg.items():
            calls = b["calls"]
            result[provider] = {
                "cost_per_call": round(b["cost"] / calls, 6),
                "avg_latency_ms": round(b["lat"] / calls, 3),
                "success_rate": round(b["succ"] / calls, 4),
            }
        return result
