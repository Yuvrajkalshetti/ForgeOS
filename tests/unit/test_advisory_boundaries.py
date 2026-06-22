from __future__ import annotations

from pathlib import Path

from forgeos.core.advisory import Auditor, Mentor
from forgeos.core.advisory.session import AdvisorySessionStore
from forgeos.testing.guards import collect_imported_modules, find_forbidden_imports

SRC = Path(__file__).resolve().parents[2] / "src" / "forgeos"
ADVISORY = SRC / "core" / "advisory"
ORCHESTRATOR = SRC / "core" / "orchestrator"

_FORBIDDEN_VERBS = {"execute", "deploy", "merge", "approve", "commit", "apply"}


def test_advisory_does_not_import_orchestrator() -> None:
    assert find_forbidden_imports(ADVISORY, ["forgeos.core.orchestrator"]) == set()


def test_orchestrator_does_not_import_advisory() -> None:
    assert find_forbidden_imports(ORCHESTRATOR, ["forgeos.core.advisory"]) == set()


def test_advisory_cannot_mutate_learning_state() -> None:
    # Advisory must not touch the learning/approval pipeline at all.
    assert find_forbidden_imports(ADVISORY, ["forgeos.core.learning"]) == set()


def test_advisory_imports_no_execution_or_adapter_modules() -> None:
    imported = collect_imported_modules(ADVISORY)
    assert "subprocess" not in imported  # cannot execute/deploy
    assert "os" not in imported
    assert not any(m.startswith("forgeos.adapters") for m in imported)


def test_advisory_exposes_no_execute_or_approve_api() -> None:
    for cls in (Mentor, Auditor, AdvisorySessionStore):
        public = {name for name in dir(cls) if not name.startswith("_")}
        assert public.isdisjoint(_FORBIDDEN_VERBS), (cls.__name__, public & _FORBIDDEN_VERBS)
