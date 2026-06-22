from __future__ import annotations

from forgeos.core.memory.models import MemoryKind, MemoryRecord, MemoryScope, MemoryStatus


def _record(**kw: object) -> MemoryRecord:
    base: dict[str, object] = {
        "scope": MemoryScope.PROJECT,
        "kind": MemoryKind.FACT,
        "content": "the build uses uv",
    }
    base.update(kw)
    return MemoryRecord(**base)  # type: ignore[arg-type]


def test_defaults() -> None:
    record = _record()
    assert record.id.startswith("mem_")
    assert record.status is MemoryStatus.ACTIVE
    assert record.salience == 1.0
    assert record.access_count == 0
    assert record.links == []


def test_content_hash_is_deterministic() -> None:
    assert _record().content_hash() == _record().content_hash()


def test_content_hash_varies_by_scope_kind_content() -> None:
    base = _record().content_hash()
    assert _record(scope=MemoryScope.USER).content_hash() != base
    assert _record(kind=MemoryKind.EVENT).content_hash() != base
    assert _record(content="different").content_hash() != base
