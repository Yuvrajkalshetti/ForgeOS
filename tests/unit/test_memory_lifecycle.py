from __future__ import annotations

import datetime

from forgeos.catalog import Collections
from forgeos.core.learning import list_proposals
from forgeos.core.memory import (
    LifecycleManager,
    LifecyclePolicy,
    MemoryKind,
    MemoryScope,
    MemoryService,
    MemoryStatus,
)
from forgeos.core.memory.lifecycle import compute_salience, is_expired
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def _at(days: float = 0.0, seconds: float = 0.0) -> datetime.datetime:
    return T0 + datetime.timedelta(days=days, seconds=seconds)


def _manager(clock_now: datetime.datetime, policy: LifecyclePolicy | None = None):
    store = InMemoryStorage()
    service = MemoryService(store, clock=lambda: clock_now)
    return service, store, LifecycleManager(service, store, policy)


def test_is_expired_pure() -> None:
    service, _, _ = _manager(T0)
    rec = service.add(MemoryScope.SESSION, MemoryKind.FACT, "x")
    assert not is_expired(rec, _at(seconds=5), 10)
    assert is_expired(rec, _at(seconds=20), 10)


def test_compute_salience_halves_at_half_life() -> None:
    service, _, _ = _manager(T0)
    rec = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "x")
    assert compute_salience(rec, _at(days=14), 14.0) == 0.5
    assert compute_salience(rec, _at(days=0), 14.0) == 1.0


def test_session_memory_expires_and_is_deleted() -> None:
    service, _, manager = _manager(T0)
    rec = service.add(MemoryScope.SESSION, MemoryKind.FACT, "x", ttl_seconds=10)
    report = manager.gc(_at(seconds=60))
    assert report.expired_session == [rec.id]
    assert service.get(rec.id) is None


def test_durable_memory_with_ttl_is_archived_not_deleted() -> None:
    service, _, manager = _manager(T0)
    rec = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "x", ttl_seconds=10)
    report = manager.gc(_at(seconds=60))
    assert report.archived_durable == [rec.id]
    stored = service.get(rec.id)
    assert stored is not None
    assert stored.status is MemoryStatus.ARCHIVED


def test_durable_memory_without_ttl_is_never_evicted() -> None:
    service, _, manager = _manager(T0)
    rec = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "x")
    manager.gc(_at(days=365))
    stored = service.get(rec.id)
    assert stored is not None
    assert stored.status is MemoryStatus.ACTIVE


def test_decay_updates_salience() -> None:
    service, _, manager = _manager(T0)
    rec = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "x")
    report = manager.gc(_at(days=14))
    assert report.decayed == 1
    stored = service.get(rec.id)
    assert stored is not None
    assert stored.salience == 0.5


def test_promotion_proposal_emitted_for_recurring_session_memory() -> None:
    store = InMemoryStorage()
    service = MemoryService(store, clock=lambda: T0)
    rec = service.add(MemoryScope.SESSION, MemoryKind.FACT, "recurring")
    rec.access_count = 3  # met threshold
    service.save(rec)

    manager = LifecycleManager(service, store, LifecyclePolicy())
    report = manager.gc(T0)  # not expired (just accessed)
    assert len(report.promotion_proposals) == 1
    proposals = list_proposals(store)
    assert proposals[0].kind == "memory.promotion"
    assert proposals[0].status.value == "proposed"  # never auto-applied


def test_consolidation_proposal_for_durable_duplicates() -> None:
    store = InMemoryStorage()
    service = MemoryService(store, clock=lambda: T0)
    service.add(MemoryScope.PROJECT, MemoryKind.FACT, "same")
    service.add(MemoryScope.PROJECT, MemoryKind.FACT, "same", dedup=False)

    manager = LifecycleManager(service, store, LifecyclePolicy())
    report = manager.gc(T0)
    assert len(report.consolidation_proposals) == 1
    assert list_proposals(store)[0].kind == "memory.consolidation"


def test_gc_emits_no_proposals_for_clean_store() -> None:
    service, store, manager = _manager(T0)
    service.add(MemoryScope.PROJECT, MemoryKind.FACT, "unique")
    report = manager.gc(T0)
    assert report.promotion_proposals == []
    assert report.consolidation_proposals == []
    assert store.query(Collections.PROPOSALS) == []
