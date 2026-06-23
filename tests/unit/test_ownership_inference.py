from __future__ import annotations

from pathlib import Path

from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine
from forgeos.core.ownership_intel import classify
from forgeos.core.ownership_intel.models import OwnershipRule
from forgeos.testing.fakes import InMemoryStorage


def _graph(tmp_path: Path) -> ExecGraphStore:
    (tmp_path / "exec.py").write_text("def place_order():\n    pass\n", encoding="utf-8")
    (tmp_path / "strat.py").write_text(
        "from exec import place_order\n\n\ndef run():\n    place_order()\n", encoding="utf-8"
    )
    store = ExecGraphStore(InMemoryStorage())
    ExecIntelEngine(store).scan(tmp_path)
    return store


def test_declared_and_observed_disagree(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    rules = [
        OwnershipRule("path", "exec.py", domain="Execution Domain", criticality="P0", impact="LIVE"),
        OwnershipRule("path", "strat.py", domain="Strategy Domain"),
    ]
    res = classify(store, "func:exec.py#place_order", rules)
    assert res.declared_owner == "Execution Domain"
    assert res.observed_owner == "Strategy Domain"
    assert res.agreement is False
    assert res.criticality == "P0"
    assert res.impact == "LIVE"
    assert 0.0 < res.confidence <= 1.0


def test_declared_only_when_no_callers(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    rules = [OwnershipRule("name", "^run$", domain="Strategy Domain")]
    res = classify(store, "func:strat.py#run", rules)
    assert res.declared_owner == "Strategy Domain"
    assert res.observed_owner == "Unknown"
    assert res.matched_by == "name"


def test_deterministic_across_runs(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    rules = [OwnershipRule("path", "exec.py", domain="Execution Domain")]
    first = classify(store, "func:exec.py#place_order", rules)
    second = classify(store, "func:exec.py#place_order", rules)
    assert first == second
