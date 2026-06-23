"""Runtime ownership summary (V2, E4 — ADR 0016).

Composes a symbol's declared/observed ownership with its consumers (callers) and
dependencies (callees) from the E2/E3 call graph. Deterministic, provider-free.
"""

from __future__ import annotations

from typing import Any

from forgeos.core.exec_intel.models import Confidence
from forgeos.core.exec_intel.query import callees, callers
from forgeos.core.exec_intel.store import ExecGraphStore
from forgeos.core.ownership_intel.classifier import classify, declared_domain
from forgeos.core.ownership_intel.models import OwnershipRule


def _with_domain(store: ExecGraphStore, node_id: str, rules: list[OwnershipRule]) -> dict[str, str]:
    node = store.get_node(node_id)
    label = node.label if node is not None else node_id
    return {"id": node_id, "label": label, "domain": declared_domain(store, node_id, rules)}


def runtime_summary(
    store: ExecGraphStore, node_id: str, rules: list[OwnershipRule]
) -> dict[str, Any]:
    """Ownership + consumers + dependencies + governance labels for one symbol."""
    result = classify(store, node_id, rules)
    consumers = [
        _with_domain(store, cid, rules)
        for cid in callers(store, node_id, 1, Confidence.RESOLVED)
    ]
    dependencies = [
        _with_domain(store, cid, rules)
        for cid in callees(store, node_id, 1, Confidence.RESOLVED)
    ]
    return {
        "symbol": node_id,
        "declared_owner": result.declared_owner,
        "observed_owner": result.observed_owner,
        "agreement": result.agreement,
        "confidence": result.confidence,
        "layer": result.layer,
        "criticality": result.criticality,
        "impact": result.impact,
        "consumers": consumers,
        "dependencies": dependencies,
    }
