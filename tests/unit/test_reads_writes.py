from __future__ import annotations

from pathlib import Path

from forgeos.core.dataflow_intel import DataFlowEngine, DataFlowStore, DfEdgeType
from forgeos.testing.fakes import InMemoryStorage


def _scan(tmp_path: Path, source: str):
    (tmp_path / "m.py").write_text(source, encoding="utf-8")
    store = DataFlowStore(InMemoryStorage())
    result = DataFlowEngine(store).scan(tmp_path)
    return store, result


def test_self_attr_reads_and_writes_are_edged(tmp_path: Path) -> None:
    store, result = _scan(
        tmp_path,
        "class A:\n"
        "    def w(self):\n"
        "        self.x = 1\n"
        "    def r(self):\n"
        "        return self.x\n",
    )
    writes = [e for e in store.edges() if e.type is DfEdgeType.WRITES]
    reads = [e for e in store.edges() if e.type is DfEdgeType.READS]
    assert any(e.dst_id == "state:m.py#A.x" and e.src_id == "func:m.py#A.w" for e in writes)
    assert any(e.dst_id == "state:m.py#A.x" and e.src_id == "func:m.py#A.r" for e in reads)
    assert result.resolved_self >= 2


def test_annotation_resolved_counted_not_edged(tmp_path: Path) -> None:
    store, result = _scan(
        tmp_path,
        "class TradeState:\n"
        "    stop_loss: float\n\n"
        "class EntryEngine:\n"
        "    def run(self, state: TradeState) -> None:\n"
        "        state.stop_loss = 1.0\n",
    )
    assert result.resolved_annotation >= 1
    # cross-object write is measured but NOT emitted in E5A
    assert all(e.dst_id != "state:m.py#TradeState.stop_loss" for e in store.edges())


def test_constructor_resolved_counted(tmp_path: Path) -> None:
    _store, result = _scan(
        tmp_path,
        "class TradeState:\n    stop_loss: float\n\n"
        "def make():\n    s = TradeState()\n    s.stop_loss = 2\n",
    )
    assert result.resolved_constructor >= 1


def test_unresolved_counted(tmp_path: Path) -> None:
    _store, result = _scan(tmp_path, "def f(x):\n    return x.value\n")
    assert result.unresolved >= 1
    assert 0.0 <= result.resolution_rate <= 1.0


def test_idempotent_rescan(tmp_path: Path) -> None:
    store, _ = _scan(tmp_path, "class A:\n    def w(self):\n        self.x = 1\n")
    first = store.edge_ids()
    DataFlowEngine(store).scan(tmp_path)
    assert store.edge_ids() == first
