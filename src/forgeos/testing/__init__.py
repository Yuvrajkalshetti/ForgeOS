"""Test doubles and static guards used across the suite."""

from __future__ import annotations

from forgeos.testing.fakes import (
    FailIfCalledProvider,
    FakeProvider,
    FakeTokenizer,
    InMemoryStorage,
    NullVectorStore,
)
from forgeos.testing.guards import collect_imported_modules, find_forbidden_imports

__all__ = [
    "FailIfCalledProvider",
    "FakeProvider",
    "FakeTokenizer",
    "InMemoryStorage",
    "NullVectorStore",
    "collect_imported_modules",
    "find_forbidden_imports",
]
