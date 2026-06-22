from __future__ import annotations

from pathlib import Path

from forgeos.core.repo_intel.hotspots import git_churn, null_churn, rank_hotspots


def test_rank_hotspots_orders_by_churn_then_path() -> None:
    churn = {"b.py": 5, "a.py": 5, "c.py": 9}
    ranked = rank_hotspots(churn)
    assert [(h.path, h.churn) for h in ranked] == [("c.py", 9), ("a.py", 5), ("b.py", 5)]


def test_rank_hotspots_limit() -> None:
    churn = {f"f{i}.py": i for i in range(20)}
    assert len(rank_hotspots(churn, limit=3)) == 3


def test_null_churn_is_empty(tmp_path: Path) -> None:
    assert null_churn(tmp_path) == {}


def test_git_churn_on_non_repo_is_graceful(tmp_path: Path) -> None:
    # Not a git repo (and git may be unavailable) — must return {} without error.
    assert git_churn(tmp_path) == {}
