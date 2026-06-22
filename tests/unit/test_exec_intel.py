from __future__ import annotations

from pathlib import Path

from forgeos.core.exec_intel import (
    ExecEdgeType,
    ExecGraphStore,
    ExecIntelEngine,
    ExecNodeType,
)
from forgeos.core.exec_intel.models import Confidence
from forgeos.testing.fakes import InMemoryStorage


def test_extracts_functions_methods_classes(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    engine = ExecIntelEngine(store)
    (tmp_path / "m.py").write_text(
        "def top():\n    pass\n\nclass A:\n    def method(self):\n        pass\n",
        encoding="utf-8",
    )
    result = engine.scan(tmp_path)
    assert result.functions == 1
    assert result.methods == 1
    assert result.classes == 1
    labels = {n.label for n in store.nodes()}
    assert {"top", "A", "A.method"} <= labels
    # DEFINES: file->top, file->A, A->A.method
    assert result.defines_edges == 3


def test_extends_resolved_by_name(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    engine = ExecIntelEngine(store)
    (tmp_path / "m.py").write_text(
        "class Base:\n    pass\n\nclass Child(Base):\n    pass\n", encoding="utf-8"
    )
    engine.scan(tmp_path)
    extends = [e for e in store.edges() if e.type is ExecEdgeType.EXTENDS]
    assert len(extends) == 1
    assert extends[0].confidence is Confidence.HEURISTIC


def test_idempotent_rescan(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    engine = ExecIntelEngine(store)
    (tmp_path / "m.py").write_text("def f():\n    pass\n", encoding="utf-8")
    engine.scan(tmp_path)
    first_nodes = store.node_ids()
    first_edges = store.edge_ids()
    engine.scan(tmp_path)
    assert store.node_ids() == first_nodes
    assert store.edge_ids() == first_edges


def test_stale_symbols_removed(tmp_path: Path) -> None:
    store = ExecGraphStore(InMemoryStorage())
    engine = ExecIntelEngine(store)
    f = tmp_path / "m.py"
    f.write_text("def f():\n    pass\n\ndef g():\n    pass\n", encoding="utf-8")
    engine.scan(tmp_path)
    assert any(n.label == "g" for n in store.nodes(ExecNodeType.FUNCTION))
    f.write_text("def f():\n    pass\n", encoding="utf-8")
    engine.scan(tmp_path)
    assert not any(n.label == "g" for n in store.nodes(ExecNodeType.FUNCTION))
