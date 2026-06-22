"""Auditor — post-hoc advisory agent (ADR 0010).

Auditor validates outcomes against evidence and is skeptical by default: claims
without evidence are not facts, and missing evidence is called out explicitly. It
**only** emits an ``AuditFinding`` node (plus ``audits`` edges); it never executes,
approves, or mutates execution/learning state.
"""

from __future__ import annotations

import datetime
import json
from collections.abc import Callable, Sequence

from forgeos._time import utcnow
from forgeos.core.advisory.models import AdvisorProvider, AuditFinding
from forgeos.core.context_assembly.models import ContextBundle
from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.ports.provider import Message, ProviderPort, ProviderRequest

Clock = Callable[[], datetime.datetime]

AUDITOR_SYSTEM = (
    "You are Auditor: an independent, skeptical engineering auditor. Validate "
    "implementation, architecture compliance, testing, and acceptance criteria "
    "against EVIDENCE. Treat claims without evidence as unverified and explicitly "
    "call out missing evidence. Identify violations, unsupported conclusions, "
    "unnecessary complexity, and risks. You never execute, approve, or implement. "
    "Respond ONLY with a JSON object with keys: evidence_review, "
    "architecture_compliance, test_coverage, recommendation, confidence (strings), "
    "risks, violations (arrays of strings)."
)


class Auditor:
    """Provider-backed auditor. Emits findings only."""

    name = "auditor"

    def __init__(self, provider: ProviderPort, graph: GraphStore, clock: Clock = utcnow) -> None:
        self._provider = provider
        self._graph = graph
        self._clock = clock

    async def audit(
        self,
        scope: str,
        *,
        model: str,
        evidence: str = "",
        grounding: ContextBundle | None = None,
        targets: Sequence[str] | None = None,
    ) -> AuditFinding:
        """Produce an evidence-based finding for ``scope`` and persist it.

        ``grounding`` is a ForgeOS-assembled :class:`ContextBundle` (P6.6) carrying
        acceptance criteria, related decisions, past findings, cards, and evidence.
        """
        grounding_text = grounding.render() if grounding is not None else ""
        parts = [f"Scope: {scope}", grounding_text]
        if evidence:
            parts.append(f"Evidence:\n{evidence}")
        user = "\n\n".join(part for part in parts if part)
        result = await self._provider.generate(
            ProviderRequest(
                messages=[Message("system", AUDITOR_SYSTEM), Message("user", user)],
                model=model,
            )
        )
        data = json.loads(result.text)
        finding = AuditFinding(
            scope=scope,
            evidence_review=str(data.get("evidence_review", "")),
            architecture_compliance=str(data.get("architecture_compliance", "")),
            test_coverage=str(data.get("test_coverage", "")),
            risks=list(data.get("risks", [])),
            violations=list(data.get("violations", [])),
            recommendation=str(data.get("recommendation", "")),
            confidence=str(data.get("confidence", "")),
            grounding_refs=[item.ref for item in grounding.items] if grounding else [],
            provider=AdvisorProvider(name=self._provider.name, model=model),
            created_at=self._clock().isoformat(),
        )
        self._graph.upsert_node(
            NodeType.AUDIT_FINDING,
            label=scope[:80],
            props=finding.model_dump(mode="json"),
            node_id=finding.id,
        )
        for target in targets or []:
            if self._graph.get_node(target) is not None:
                self._graph.add_edge(finding.id, target, EdgeType.AUDITS)
        return finding
