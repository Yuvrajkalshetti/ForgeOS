from __future__ import annotations

from pathlib import Path

from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine
from forgeos.core.ownership_intel import runtime_summary
from forgeos.core.ownership_intel.models import OwnershipRule
from forgeos.testing.fakes import InMemoryStorage


def test_summary_lists_consumers_and_dependencies(tmp_path: Path) -> None:
    (tmp_path / "exec.py").write_text(
        "def broker():\n    pass\n\ndef place_order():\n    broker()\n", encoding="utf-8"
    )
    (tmp_path / "strat.py").write_text(
        "from exec import place_order\n\n\ndef run():\n    place_order()\n", encoding="utf-8"
    )
    store = ExecGraphStore(InMemoryStorage())
    ExecIntelEngine(store).scan(tmp_path)
    rules = [
        OwnershipRule("path", "exec.py", domain="Execution Domain"),
        OwnershipRule("path", "strat.py", domain="Strategy Domain"),
    ]
    summary = runtime_summary(store, "func:exec.py#place_order", rules)
    consumer_ids = {c["id"] for c in summary["consumers"]}
    dep_ids = {d["id"] for d in summary["dependencies"]}
    assert "func:strat.py#run" in consumer_ids
    assert "func:exec.py#broker" in dep_ids
    assert summary["declared_owner"] == "Execution Domain"
