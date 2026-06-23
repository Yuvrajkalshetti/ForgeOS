from __future__ import annotations

from pathlib import Path

from forgeos.core.exec_intel import ExecEdgeType, ExecGraphStore, ExecIntelEngine
from forgeos.core.exec_intel.models import Confidence
from forgeos.testing.fakes import InMemoryStorage


def _calls(store: ExecGraphStore) -> list[tuple[str, str]]:
    return [(e.src_id, e.dst_id) for e in store.edges() if e.type is ExecEdgeType.CALLS]


def test_intra_file_call(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    (tmp_path / "m.py").write_text("def g():\n    pass\n\ndef f():\n    g()\n", encoding="utf-8")
    result = ExecIntelEngine(store).scan(tmp_path)
    assert ("func:m.py#f", "func:m.py#g") in _calls(store)
    assert result.calls_edges >= 1


def test_self_method_call(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    (tmp_path / "m.py").write_text(
        "class A:\n    def a(self):\n        self.b()\n    def b(self):\n        pass\n",
        encoding="utf-8",
    )
    ExecIntelEngine(store).scan(tmp_path)
    assert ("func:m.py#A.a", "func:m.py#A.b") in _calls(store)


def test_cross_file_import_call(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    (tmp_path / "a.py").write_text("def helper():\n    pass\n", encoding="utf-8")
    (tmp_path / "b.py").write_text(
        "from a import helper\n\n\ndef use():\n    helper()\n", encoding="utf-8"
    )
    ExecIntelEngine(store).scan(tmp_path)
    assert ("func:b.py#use", "func:a.py#helper") in _calls(store)


def test_unresolved_calls_counted_not_edged(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    (tmp_path / "m.py").write_text("def f(x):\n    x.run()\n", encoding="utf-8")
    result = ExecIntelEngine(store).scan(tmp_path)
    assert result.unresolved_calls >= 1
    assert _calls(store) == []


def test_resolved_calls_have_resolved_confidence(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    (tmp_path / "m.py").write_text("def g():\n    pass\n\ndef f():\n    g()\n", encoding="utf-8")
    ExecIntelEngine(store).scan(tmp_path)
    call_edges = [e for e in store.edges() if e.type is ExecEdgeType.CALLS]
    assert call_edges
    assert all(e.confidence is Confidence.RESOLVED for e in call_edges)
