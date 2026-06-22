from __future__ import annotations

from forgeos.ports.storage import StoragePort
from forgeos.testing.fakes import InMemoryStorage


def test_in_memory_storage_satisfies_protocol() -> None:
    # StoragePort is runtime_checkable; the fake must structurally satisfy it.
    assert isinstance(InMemoryStorage(), StoragePort)
