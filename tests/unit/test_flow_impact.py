from __future__ import annotations

from pathlib import Path

from forgeos.core.dataflow_intel import DataFlowEngine, DataFlowStore
from forgeos.core.dataflow_intel.query import flow_impact
from forgeos.core.exec_intel import ExecGraphStore
from forgeos.testing.fakes import InMemoryStorage


def test_flow_impact_lists_readers_and_writers(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text(
        "class A:\n"
        "    def w(self):\n"
        "        self.x = 1\n"
        "    def r(self):\n"
        "        return self.x\n",
        encoding="utf-8",
    )
    store = InMemoryStorage()
    df = DataFlowStore(store)
    DataFlowEngine(df).scan(tmp_path)
    affected = flow_impact(df, ExecGraphStore(store), "state:m.py#A.x")
    assert "func:m.py#A.w" in affected
    assert "func:m.py#A.r" in affected
