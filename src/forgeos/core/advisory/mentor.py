"""Mentor — pre-execution advisory agent (ADR 0010).

Mentor reasons through a request and produces a structured implementation strategy.
It challenges assumptions and prioritizes truth over agreement. It **only** emits a
``MentorRecommendation`` node (plus ``advises``/``informs`` edges); it never executes,
approves, or mutates execution/learning state.
"""

from __future__ import annotations

import datetime
import json
from collections.abc import Callable, Sequence

from forgeos._time import utcnow
from forgeos.core.advisory.models import AdvisorProvider, MentorRecommendation
from forgeos.core.context_assembly.models import ContextBundle
from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.ports.provider import Message, ProviderPort, ProviderRequest

Clock = Callable[[], datetime.datetime]

MENTOR_SYSTEM = (
    "You are Mentor: a technical architect and implementation advisor. Think through "
    "the problem and guide toward the best implementation strategy. Challenge "
    "assumptions, force specificity, identify risks and gaps, prevent over- and "
    "under-engineering, and prefer simplicity. Prioritize truth over agreement; do "
    "NOT automatically agree. You never execute, approve, or implement. Respond ONLY "
    "with a JSON object with keys: kind (proposal|question|request), understanding "
    "(string), assumptions, challenges, gaps, alternatives, proposed_plan (arrays of "
    "strings), recommendation (string), confidence (string)."
)


class Mentor:
    """Provider-backed advisor. Emits recommendations only."""

    name = "mentor"

    def __init__(self, provider: ProviderPort, graph: GraphStore, clock: Clock = utcnow) -> None:
        self._provider = provider
        self._graph = graph
        self._clock = clock

    async def advise(
        self,
        request: str,
        *,
        model: str,
        context: str = "",
        grounding: ContextBundle | None = None,
        targets: Sequence[str] | None = None,
    ) -> MentorRecommendation:
        """Produce a recommendation for ``request`` and persist it as a graph node.

        ``grounding`` is a ForgeOS-assembled :class:`ContextBundle` (P6.6); its
        rendered, budgeted text is supplied to the provider as grounded context.
        """
        grounding_text = grounding.render() if grounding is not None else ""
        user = "\n\n".join(part for part in [request, grounding_text, context] if part)
        result = await self._provider.generate(
            ProviderRequest(
                messages=[Message("system", MENTOR_SYSTEM), Message("user", user)],
                model=model,
            )
        )
        data = json.loads(result.text)
        rec = MentorRecommendation(
            kind=str(data.get("kind", "proposal")),
            request=request,
            understanding=str(data.get("understanding", "")),
            assumptions=list(data.get("assumptions", [])),
            challenges=list(data.get("challenges", [])),
            gaps=list(data.get("gaps", [])),
            alternatives=list(data.get("alternatives", [])),
            recommendation=str(data.get("recommendation", "")),
            proposed_plan=list(data.get("proposed_plan", [])),
            confidence=str(data.get("confidence", "")),
            grounding_refs=[item.ref for item in grounding.items] if grounding else [],
            provider=AdvisorProvider(name=self._provider.name, model=model),
            created_at=self._clock().isoformat(),
        )
        self._graph.upsert_node(
            NodeType.MENTOR_RECOMMENDATION,
            label=request[:80],
            props=rec.model_dump(mode="json"),
            node_id=rec.id,
        )
        for target in targets or []:
            node = self._graph.get_node(target)
            if node is None:
                continue
            edge = EdgeType.INFORMS if node.type == NodeType.DECISION else EdgeType.ADVISES
            self._graph.add_edge(rec.id, target, edge)
        return rec
