from __future__ import annotations

import datetime

from forgeos.core.memory import MemoryKind, MemoryScope, MemoryService, MemoryStatus
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def _service() -> MemoryService:
    return MemoryService(InMemoryStorage(), clock=lambda: T0)


def test_add_and_get() -> None:
    service = _service()
    record = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "uses uv")
    fetched = service.get(record.id)
    assert fetched is not None
    assert fetched.content == "uses uv"
    assert fetched.created_at == T0


def test_dedup_returns_existing_within_scope() -> None:
    service = _service()
    first = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "dup")
    second = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "dup")
    assert first.id == second.id
    assert len(service.query()) == 1


def test_dedup_disabled_creates_duplicate() -> None:
    service = _service()
    service.add(MemoryScope.PROJECT, MemoryKind.FACT, "dup")
    service.add(MemoryScope.PROJECT, MemoryKind.FACT, "dup", dedup=False)
    assert len(service.query()) == 2


def test_same_content_different_scope_not_deduped() -> None:
    service = _service()
    service.add(MemoryScope.PROJECT, MemoryKind.FACT, "x")
    service.add(MemoryScope.USER, MemoryKind.FACT, "x")
    assert len(service.query()) == 2


def test_query_filters_by_scope_and_kind() -> None:
    service = _service()
    service.add(MemoryScope.PROJECT, MemoryKind.FACT, "a")
    service.add(MemoryScope.PROJECT, MemoryKind.EVENT, "b")
    service.add(MemoryScope.USER, MemoryKind.FACT, "c")
    assert len(service.query(scope=MemoryScope.PROJECT)) == 2
    assert len(service.query(kind=MemoryKind.FACT)) == 2
    assert len(service.query(scope=MemoryScope.USER, kind=MemoryKind.FACT)) == 1


def test_touch_bumps_access_and_restores_salience() -> None:
    later = datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)
    clock = {"now": T0}
    service = MemoryService(InMemoryStorage(), clock=lambda: clock["now"])
    record = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "a")
    record.salience = 0.3
    service.save(record)

    clock["now"] = later
    touched = service.touch(record.id)
    assert touched is not None
    assert touched.access_count == 1
    assert touched.salience == 1.0
    assert touched.last_accessed_at == later


def test_delete_removes_record() -> None:
    service = _service()
    record = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "a")
    service.delete(record.id)
    assert service.get(record.id) is None


def test_archived_excluded_by_status_filter() -> None:
    service = _service()
    record = service.add(MemoryScope.PROJECT, MemoryKind.FACT, "a")
    record.status = MemoryStatus.ARCHIVED
    service.save(record)
    assert service.query(status=MemoryStatus.ACTIVE) == []
    assert len(service.query(status=MemoryStatus.ARCHIVED)) == 1
