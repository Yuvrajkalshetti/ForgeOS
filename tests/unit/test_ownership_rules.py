from __future__ import annotations

from pathlib import Path

from forgeos.core.ownership_intel.rules import DEFAULT_RULES, load_rules


def test_defaults_when_no_project_file(tmp_path: Path) -> None:
    assert load_rules(tmp_path) == list(DEFAULT_RULES)


def test_project_rules_take_precedence(tmp_path: Path) -> None:
    (tmp_path / ".forgeos").mkdir()
    (tmp_path / ".forgeos" / "ownership.yaml").write_text(
        "rules:\n"
        "  - match: {name: '^ExecutionService'}\n"
        "    domain: Execution Domain\n"
        "    criticality: P0\n",
        encoding="utf-8",
    )
    rules = load_rules(tmp_path)
    assert rules[0].domain == "Execution Domain"
    assert rules[0].criticality == "P0"
    assert rules[0].match_kind == "name"


def test_malformed_entries_skipped(tmp_path: Path) -> None:
    (tmp_path / ".forgeos").mkdir()
    (tmp_path / ".forgeos" / "ownership.yaml").write_text(
        "rules:\n  - not_a_match: true\n  - match: {path: 'app/*'}\n    layer: Service\n",
        encoding="utf-8",
    )
    rules = load_rules(tmp_path)
    assert any(r.pattern == "app/*" and r.layer == "Service" for r in rules)
