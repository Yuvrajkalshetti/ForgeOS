"""Memory lifecycle management (plan §5).

Deterministic and local. Three mechanisms run during garbage collection:

* **TTL expiry** — session memory idle past its TTL is evicted (session is
  ephemeral). Durable scopes are never auto-deleted (archive-first).
* **Decay** — ``salience`` is recomputed as a pure exponential function of recency
  (time since last access). No learned scoring, no embeddings.
* **Promotion / consolidation** — recurring session memory and duplicate durable
  memory generate *Learning proposals*; nothing is applied without human approval.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from forgeos.core.learning.proposal import emit_proposal
from forgeos.core.memory.models import MemoryRecord, MemoryScope, MemoryStatus
from forgeos.core.memory.service import MemoryService
from forgeos.ports.storage import StoragePort

_DURABLE_SCOPES = (MemoryScope.PROJECT, MemoryScope.USER)


@dataclass(frozen=True)
class LifecyclePolicy:
    """Tunable, deterministic lifecycle thresholds."""

    session_ttl_seconds: int = 86_400  # 24h idle
    decay_half_life_days: float = 14.0
    promotion_access_threshold: int = 3


@dataclass
class GcReport:
    """Outcome of a garbage-collection pass (for observability / CLI output)."""

    expired_session: list[str] = field(default_factory=list)
    archived_durable: list[str] = field(default_factory=list)
    decayed: int = 0
    promotion_proposals: list[str] = field(default_factory=list)
    consolidation_proposals: list[str] = field(default_factory=list)


def is_expired(record: MemoryRecord, now: datetime.datetime, ttl_seconds: int) -> bool:
    """True if ``record`` has been idle longer than ``ttl_seconds``."""
    idle = (now - record.last_accessed_at).total_seconds()
    return idle > ttl_seconds


def compute_salience(
    record: MemoryRecord, now: datetime.datetime, half_life_days: float
) -> float:
    """Recency-based salience in (0, 1]: ``0.5 ** (idle_days / half_life)``."""
    idle_days = max(0.0, (now - record.last_accessed_at).total_seconds() / 86_400)
    return float(0.5 ** (idle_days / half_life_days))


class LifecycleManager:
    """Runs deterministic garbage collection over the memory store."""

    def __init__(
        self,
        service: MemoryService,
        store: StoragePort,
        policy: LifecyclePolicy | None = None,
    ) -> None:
        self._service = service
        self._store = store
        self._policy = policy or LifecyclePolicy()

    def gc(self, now: datetime.datetime) -> GcReport:
        """Expire/archive, decay, and propose. Returns a report; applies no promotions."""
        report = GcReport()
        active = self._service.query(status=MemoryStatus.ACTIVE)

        for record in active:
            ttl = self._effective_ttl(record)
            if ttl is not None and is_expired(record, now, ttl):
                if record.scope == MemoryScope.SESSION:
                    self._service.delete(record.id)  # session is ephemeral
                    report.expired_session.append(record.id)
                else:
                    record.status = MemoryStatus.ARCHIVED  # durable: archive, never delete
                    self._service.save(record)
                    report.archived_durable.append(record.id)
                continue
            new_salience = compute_salience(record, now, self._policy.decay_half_life_days)
            if new_salience != record.salience:
                record.salience = new_salience
                self._service.save(record)
                report.decayed += 1

        self._propose_promotions(now, report)
        self._propose_consolidations(now, report)
        return report

    def _effective_ttl(self, record: MemoryRecord) -> int | None:
        """Per-record TTL overrides; else session scope uses the policy TTL."""
        if record.ttl_seconds is not None:
            return record.ttl_seconds
        if record.scope == MemoryScope.SESSION:
            return self._policy.session_ttl_seconds
        return None

    def _propose_promotions(self, now: datetime.datetime, report: GcReport) -> None:
        for record in self._service.query(
            scope=MemoryScope.SESSION, status=MemoryStatus.ACTIVE
        ):
            if record.access_count >= self._policy.promotion_access_threshold:
                proposal = emit_proposal(
                    self._store,
                    kind="memory.promotion",
                    payload={"memory_id": record.id, "target_scope": "project"},
                    evidence=[f"accessed {record.access_count}x in session"],
                    benefits="reuse a recurring session fact across the project",
                    risks="may promote a transient detail",
                    reuse_value="high" if record.access_count >= 5 else "medium",
                    clock=lambda: now,
                )
                report.promotion_proposals.append(proposal.id)

    def _propose_consolidations(self, now: datetime.datetime, report: GcReport) -> None:
        for scope in _DURABLE_SCOPES:
            groups: dict[str, list[str]] = {}
            for record in self._service.query(scope=scope, status=MemoryStatus.ACTIVE):
                groups.setdefault(record.content_hash(), []).append(record.id)
            for ids in groups.values():
                if len(ids) > 1:
                    proposal = emit_proposal(
                        self._store,
                        kind="memory.consolidation",
                        payload={"scope": scope.value, "memory_ids": sorted(ids)},
                        evidence=[f"{len(ids)} duplicate records in {scope.value}"],
                        benefits="merge duplicates to cut tokens and noise",
                        risks="merge could drop a subtle distinction",
                        reuse_value="medium",
                        clock=lambda: now,
                    )
                    report.consolidation_proposals.append(proposal.id)
